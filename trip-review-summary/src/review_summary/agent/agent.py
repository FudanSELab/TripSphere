import os
from collections.abc import AsyncIterable
from typing import Any, Literal, Dict, List
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class AgentState(BaseModel):
    messages: List[BaseMessage]
    structured_response: ResponseFormat = None


@tool
def get_attraction_id(
    attraction_name: str,
):
    """Use this to get the ID of an attraction based on its name.

    Args:
        attraction_name: The name of the attraction to get the ID for.

    Returns:
        A dictionary containing the attraction ID, or an error message if
        the request fails.
    """
    # Tool implementation would go here
    pass


@tool
def get_reviews(
    business_id: str,
    max_reviews: int = 10,
):
    """Use this to get reviews for a business.

    Args:
        business_id: The ID of the business to get reviews for.
        max_reviews: Maximum number of reviews to retrieve. Defaults to 10.

    Returns:
        A dictionary containing the reviews data, or an error message if
        the request fails.
    """
    # Tool implementation would go here
    pass


class ReviewSummarizerAgent:
    """ReviewSummarizerAgent - a specialized assistant for summarizing business reviews."""

    SYSTEM_INSTRUCTION = (
        'You are a review summarizer. Your role is to analyze customer reviews retrieved using the get_reviews tool '
        'and provide concise, accurate summaries that answer the user\'s specific questions about the business. '
        'First, use the get_attraction_id tool to find the attraction ID based on the name provided by the user. '
        'Then, use the get_reviews tool to retrieve reviews for that attraction. '
        'Finally, analyze the reviews and provide a summary that answers the user\'s specific questions. '
        'You should focus on key themes, sentiment, and specific aspects mentioned in the reviews. '
        'Always base your responses strictly on the review content you receive from the tool. '
        'If the reviews don\'t contain information relevant to the user\'s question, acknowledge this limitation. '
        'Be objective and factual in your summaries, highlighting both positive and negative aspects when present.'
    )

    FORMAT_INSTRUCTION = (
        'Set response status to input_required if the user needs to provide more information to complete the request.'
        'Set response status to error if there is an error while processing the request.'
        'Set response status to completed if the request is complete.'
    )

    def __init__(self):
        # Always use OpenAI model
        self.model = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            openai_api_key=os.getenv('API_KEY', 'EMPTY'),
            openai_api_base=os.getenv('TOOL_LLM_URL'),
            temperature=0,
        )
        self.tools = [get_attraction_id, get_reviews]
        
        # Create the graph
        self.graph = self._create_graph()

    def _create_graph(self):
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_call_tool,
            {
                "continue": "tools",
                "end": "agent"
            }
        )
        workflow.add_edge("tools", "agent")
        
        # Set finish point
        workflow.set_finish_point("agent")
        
        return workflow.compile(checkpointer=MemorySaver())

    def _call_model(self, state: AgentState):
        # Prepare messages for the model
        messages = [AIMessage(content=self.SYSTEM_INSTRUCTION, type="system")] + state.messages
        response = self.model.invoke(messages, {"response_format": ResponseFormat})
        return {"messages": [response]}

    def _should_call_tool(self, state: AgentState):
        # Check if the last message has tool calls
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": context_id}}
        
        # Stream the execution
        async for event in self.graph.astream(inputs, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_message = event["messages"][-1]
                
                if isinstance(last_message, AIMessage) and last_message.tool_calls:
                    # Check which tool is being called to provide appropriate feedback
                    tool_names = [tc.get('name', '') for tc in last_message.tool_calls]
                    if 'get_attraction_id' in tool_names:
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': 'Looking up attraction ID...',
                        }
                    elif 'get_reviews' in tool_names:
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': 'Retrieving reviews for analysis...',
                        }
                    else:
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': 'Processing with tools...',
                        }
                elif isinstance(last_message, ToolMessage):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Analyzing the reviews..',
                    }

        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        if hasattr(current_state.values, 'messages') and current_state.values.messages:
            last_message = current_state.values.messages[-1]
            if hasattr(last_message, 'additional_kwargs') and 'response_format' in last_message.additional_kwargs:
                structured_response = last_message.additional_kwargs['response_format']
            else:
                structured_response = None
        else:
            structured_response = None
            
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']



