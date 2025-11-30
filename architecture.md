# Architecture

```
谢森煜 李展发 张之麒 顾若楠 Modified November 23
```
## 各微服务/Agent

聊天服务（trip-chat-service）[ (^) 谢森煜 ]
**Overview**
接收来自用户的自然语言请求，管理用户对话，同时也负责Memory细粒度操作（Operations）、消息推流等
等。
**组件内部细节**
实现语言：Python
使用MongoDB作为存储数据库，管理用户和聊天助手（trip-chat-assistant）之间的原始对话记录。
借鉴MemOS（http://arxiv.org/abs/2507.03724）的思想，聊天服务（trip-chat-service）也实现了记忆机制需
要的低层次的Operation操作（如不同类型记忆的转化、更新和检索）和相关基础设施，向各Agent提供统一封
装好的Reader API。这些记忆机制同时也作为聊天助手（trip-chat-assistant）的Context Provider，动态地注
入记忆。


聊天服务（trip-chat-service）为各个Agent提供了统一的对话管理和对话级记忆管理能力（其他Agent的
AgentCard注册到这个host之后再通过A2A转接），但是单次任务内的任务级记忆（如草稿、TODO列表、中间
状态、临时文件等），还是需要Agent自己管理的。

#### 组件外部属性

- RESTful API^

对外暴露聊天助手（trip-chat-assistant）的调用接口，类似ChatGPT backend的接口。

提供管理Conversation的接口，用于加载（原始）历史对话记录、删除对话、更新对话元数据等。

接口细节见Apifox（https://app.apifox.com/project/7147228）。

### 聊天助手（trip-chat-assistant）[ 谢森煜 ]

#### 1 .欢迎语/开场白，可提供若干固定的候选问题，候选问题遵循固定流程模板

```
2 .意图识别，根据用户原始问题的意图，调用trip-hotel-advisor等别的Sub Agent
3 .统一管理对话记录和对话级的Memory，并将这些能力也开放给其他服务/Agent
```

**Overview**

内嵌于聊天服务（trip-chat-service）的一个聊天助手，作为系统的Main Agent，负责交互聊天与识别用户的
意图，并基于用户意图规划行动、分派任务，可通过A2A协议调用Sub Agent的能力。

**组件内部细节**

实现语言：Python

```
1 .意图识别与任务编排
```
聊天助手（trip-chat-assistant）内嵌在trip-chat-service这个进程/容器内，在接受用户的请求后会首先进行意
图的识别，然后根据用户意图再决定是否要调用Sub Agent，因此实际上这里会覆盖到两种模式：单体的单
Agent和（基于A2A协议的）分布式多Agent。

如果用户问题属于简单咨询，如"Can I book air tickets through TripSphere?"，则Main Agent就可以搞定，这
里就属于“单体的单Agent”的模式，即一个进程同时接收用户推理请求，调用LLM后，直接给用户返回推理结
果。

如果用户问题包含了咨询酒店/景点推荐的意图，如"Is there any place in Shanghai that's good for spending
the weekend with my kids?"，则Main Agent会根据用户的意图需求调用Remote Agent的垂域任务能力，例如
这里Main Agent要通过A2A调用景点推荐（trip-attraction-advisor）这个Agent。这里就属于“分布式多
Agent”的模式。

后续版本也可以通过A2A接入智能客服、笔记推荐等等Agent。

```
2 .Memory Management
```

为了更好地支持长对话，聊天助手（trip-chat-assistant）需要拥有一套记忆管理机制。这里我选择了
MemoryOS[EMNLP 2025 Oral]（http://arxiv.org/abs/2506.06326）作为记忆管理机制的默认实现。以每个
Conversation为单元维护记忆，同时由中期记忆转化而来的长期记忆也会更新到用户服务（trip-user-service）
的用户知识库中去。

**组件外部属性**

- A2A^

该Agent不支持直接A2A通信，需要从聊天服务（trip-chat-service）发起调用，但会考虑提供一个AgentCard
对其主要能力进行说明。

### 点评服务（trip-review-service）[ 李展发 ]

**Overview**

负责酒店/景点的点评业务，一条点评包括评分、图文内容、日期、点评对象等。同时该服务也驱动着点评摘
要（trip-review-summary）生成智能化的点评摘要，或为下游任务/其他Agent提供结构化总结。

**组件内部细节**

实现语言：Go

详细方案见： 【2025-10-29】点评服务技术方案，主要需要支持创建点评、编辑点评、回复点评等功能。

关于图片添加/删除的管理，目前想到的有两种方向：

```
1 .一条点评里面包含的图片总是有限的，因此添加/删除图片&回显可以完全只在用户的浏览器上完成，然后
保存点评的时候再把用户所有的图片一次性上传，不需要每次添加一张上传一张。那么可能某次保存点评
请求的请求体中，既有已经保存在了MinIO里的图片（对应可能只是一串URL），也有刚刚要被上传的新
图片（包含完整图片数据和元数据），需要分别处理。
```

```
2 .沿用一般编辑器的思路，每次上传都调用一次上传接口/预签名URL，然后接口返回URL(s)。但是这么做需
要考虑的就是，编辑态的点评（虽然并不存在Draft这么一种Model）不一定就会被保存，此前上传的图片
其实也没用，长期继续存在MinIO就是浪费资源。因此需要设计一种机制对此进行处理，例如搞一个temp
bucket，然后用MinIO的生命周期管理能力，让temp bucket中的文件 7 天后自动删除。
```
以及，某次删除/编辑点评后，旧的不需要的图片资源需要如何被删除，也需要进一步细化出一个明确的方
案。

点评服务（trip-review-service）不像笔记服务（trip-note-service）那么复杂，不需要适配Markdown渲染/编
辑器和草稿管理啥的，前端只需要添加/删除图片+写一行txt文本，相关接口和负责开发前端的同学协商好即
可。

其实点评下面的回复或许可以直接复用评论服务（trip-comment-service）的能力？

**组件外部属性**

- gRPC^

提供接口：创建点评、更新点评、分页查询点评、创建点评回复、分页查询点评回复，查询酒店/景点点评统
计。

### 点评摘要（trip-review-summary）[ 李展发 , 刘嘉诚 ]

**Overview**

点评摘要（trip-review-summary）从大量用户点评中自动提炼关键信息，生成高质量的、动态的可读摘要，
帮助用户快速了解一个酒店/景点的整体口碑特征。充当“点评知识蒸馏器”的角色，为其他任务/Agent提供点
评知识。

**组件内部细节**

实现语言：Python

主要基于GraphRAG的思路做RAG，周期性地、动态地获取点评条目集合，并生成酒店/景点的点评摘要知识
库。

需要考虑的一个点是，老点评和新点评的参考价值不同，可能需要设计一套时间窗口淘汰机制来处理。

在知识库/图谱构建完成后，可以在点评界面生成一段静态的“智能点评摘要”（类似于饿了么商户评价中的“AI
智能评价官”），同时也能以Agent的形式向外提供点评知识的解读、检索等，也就是根据传入Query的不同意
图，动态地使用Local Search/Global Search/DRIFT Search/Question Generation。


但是由于GraphRAG的成本非常高，如果对所有的酒店/景点都构建知识图谱显然不划算，因此目前考虑只对部
分景点/酒店进行完整版的GraphRAG，同时优先考虑使用LazyGraphRAG（https://www.microsoft.com/en-
us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/）技术，也就是NLP Graph
Extractor。

```
其余的景点/酒店使用某种简化版的更低成本实现方案，或者直接就不支持也行。下个小版本在看
```
建议直接安装graphrag这个包然后定制一下配置和Prompt并适配点评服务（trip-review-service），因为
graphrag本身是模块化设计的，我们可以按需使用各个模块。GraphRAG本身是为通用文档设计的，如果真的
需要更深层次的优化/定制，再考虑我们自己重新实现（参考源代码
https://github.com/microsoft/graphrag）。

除此之外，后续也可以支持如高频词提取、情感标签提取等更多样的点评分析。

**组件外部属性**

- AgentCard^

支持A2A协议直接通讯，提供NL驱动的酒店/景点的点评解读和检索，可以参考GraphRAG。GraphRAG Query
过程的耗时一般不短，因此可以作为一个A2A后台Task来进行。

- gRPC^

提供一些点评摘要知识图谱的检索接口，这些接口比直接问Agent更快，但是结果也更简单，比如直接返回
TopK个顶层Community的一些信息等等。

前面提到的酒店/景点点评页面要展示的静态“智能点评摘要”也从这里的接口获取（需要一份默认的Query）。

以及需不需要提供几个简单的接口以供向量检索/关键词检索之类的？


### 评论服务（trip-comment-service）[ 李展发 ]

**Overview**

主要是支撑笔记（和点评？）下的评论区功能，目前先做简单评论，只需要支持文字和emoji，不需要支持图
片。

**组件内部细节**

实现语言：Go

目前只需要实现简单版评论区，参考马蜂窝（https://www.mafengwo.cn/index.php）游记下面的评论区。因
为暂时不支持对评论点赞，所以默认直接按照时间排序返回就好。

到0.2.0或0.3.0或许可以支持更多的智能能力，例如智能过滤敏感词、垃圾评论等功能。

```
对嵌套结构评论、点赞评论的支持无限期推迟......
```
**组件外部属性**

- gRPC^

需要支持用户（对某个对象）发布评论、回复（引用）评论、删除评论、编辑评论、分页查询评论等接口。

### 用户服务（trip-user-service）[ 李展发 ]

**Overview**

包含传统微服务系统中的用户信息管理，考虑到系统目前规模较小，认证鉴权也一并合入这个服务。同时这
个服务还维护了聊天服务（trip-chat-service）中记忆模块产出的用户知识，如用户偏好、用户关键事实等。

**组件内部细节**

实现语言：Java

直接复用train-ticket的ts-user-service和ts-auth-service的业务逻辑，除了最基本的用户和鉴权，还需要支持管
理聊天、任务中产生的用户动态知识。可以部署用一个向量数据库（推荐Milvus或者Qdrant）用来作为User
KB的存储支撑。

```
用户头像等功能不需要实现，等到0.2.0或0.3.0再按需从train-ticket抄过来即可。
```
**组件外部属性**

- MCP^

主要是把用户的动态知识和静态知识（用户Profile）等的检索包装为MCP工具。

- gRPC^

主要支持查询用户信息、更新用户信息、登录登出、刷新Token、授权、写入/查询/删除用户动态知识。

### 行程服务（trip-itinerary-service）[ 陈董祺 ]

**Overview**

参考携程的行程智能规划，我们实现简化版的行程——不关心如何从当前地方出发到目的地，直接默认从到了
目的地后开始规划，一个行程由多天组成，每一天内可以顺序包含若干个景点。


#### 组件内部细节

实现语言：Python

可以直接用MongoDB来存行程规划的文档，一趟行程由若干天组成（至少有 1 天），每天可以顺序地包含若干
个景点，同时还支持待安排和备注等功能。行程服务（trip-itinerary-service）也需要支持用户在前端通过请求
修改行程细节。

**组件外部属性**

- MCP^

把对行程的基本操纵的能力封装为MCP工具。

- gRPC^

支持添加新的一天、删除某一天、为某天在特定顺序处添加一个景点、删除某天特定顺序处的一个景点、

### 行程规划（trip-itinerary-planner）[ 陈董祺 ]

**Overview**

行程规划（trip-itinerary-planner）Agent主要负责根据用户的需求和指令进行多约束的复杂行程规划任务。

**组件内部细节**

实现语言：Python

详细的技术方案见： Itinerary Planner，需要支持类似携程的行程规划的能力，目前先支持一次性的生成，
生成的行程内容除了简单引用一下景点，也最好在“备注”里面写一下重点观赏、特色体验等。然后可以根据安
排的行程景点规划把住宿推荐也给出一下。

```
后续让Agent可以直接调用行程服务（trip-itinerary-service）提供的一些MCP工具对行程进行修改。
```
在行程生成后，可以和Agent交互了解旅行相关的问题，或者继续修改已有的行程（又有点像Vibe Coding
了）。

机票和美食相关的知识如果要搞的话，就得调第三方的API，目前系统不打算支持这两个模块。

**组件外部属性**

- AgentCard^

支持A2A协议直接通讯，提供NL驱动的智能行程规划。这个Agent被注册到聊天服务（trip-chat-service）后前
端就可以直接用那套API调用了。

```
通过设置字段metadata = {"agent": "itinerary-planner"}，可以直接指定让trip-itinerary-planner来处理请求
```
### 酒店服务（trip-hotel-service）[ 刘嘉诚 ]

**Overview**

管理TripSphere中酒店相关的业务，目前0.1.0只支持简单的酒店基本信息、标签筛选、地理位置等，下一个
minor release要支持房型和库存功能。

**组件内部细节**


实现语言：Java

如果使用MongoDB的话可以不需要再单独维护一个向量数据库，可以直接用MongoDB的Vector Search，可直
接支持稠密向量+关键词的混合检索。

**组件外部属性**

- MCP^

将基本的酒店信息筛选检索能力封装为MCP工具。

- gRPC^

支持添加酒店、删除酒店、更改酒店信息、查询酒店基本信息、查询酒店基础设施、条件/分页筛选查询酒
店、查询附近酒店、距离计算等接口。

### 酒店推荐（trip-hotel-advisor）[ 刘嘉诚 ]

**Overview**

个性化的酒店推荐Agent，理想上可以结合用户画像+历史行为等，再根据地理位置、价格、品牌等约束在多
轮对话中逐步锁定推荐方案。（A2A Task InputRequired）

**组件内部细节**

实现语言：Python

可以参考DeepResearch的架构实现，可以参考阿里的DeepResearch（https://github.com/Alibaba-
NLP/DeepResearch/）和LangChain的Open Deep Research（https://github.com/langchain-
ai/open_deep_research）的源代码。

```
或许可以考虑用DeepAgents框架？
```
**组件外部属性**

- AgentCard^

支持A2A协议直接通讯，提供NL驱动的酒店推荐能力。常见的需求包括“我要离XXX景点/地点比较近”、“我要
离地铁站比较近”、“我一般习惯早上起床跑一会儿跑步机”（推理出酒店需要具有健身房基础设施）......

### 景点服务（trip-attraction-service）[ 刘嘉诚 ]

**Overview**

管理TripSphere中景点相关的业务。

**组件内部细节**

实现语言：Java

如果使用MongoDB的话可以不需要再单独维护一个向量数据库，可以直接用MongoDB的Vector Search，可直
接支持稠密向量+关键词的混合检索。

**组件外部属性**

- gRPC^


#### 支持添加景点、删除景点、更新景点信息、查询景点详情、条件/分页筛选查询景点等接口。

### 景点推荐（trip-attraction-advisor）[ 刘嘉诚 ]

**Overview**

景点推荐（trip-attraction-advisor）Agent支持根据用户的需求推荐特定城市的旅游景点。

**组件内部细节**

实现语言：Java

使用Spring AI Alibaba实现，可以参考DeepResearch的架构，最后生成一个综合景点推荐报告。数据来源包括
现有景点ID、介绍、价格、地理位置等，非结构化的数据包括相关旅游攻略、用户点评等。

**组件外部属性**

- AgentCard^

支持A2A协议直接通讯，提供NL驱动的景点推荐，返回的数据最好是格式化的报告。被调用的情况主要是聊天
助手（trip-chat-assistant）可能会直接A2A调景点推荐（trip-attraction-advisor）。由于DeepResearch耗时一
般也比较久，建议返回一个Task，然后通过前端轮询或Notification Push来更新结果。

### 笔记服务（trip-note-service）[ 顾若楠 , 谢森煜 ]

**Overview**

笔记服务负责UGC的管理，用户可以发布、编辑、删除属于自己的笔记，其发布的笔记也可以被其他用户看到
（并点赞/取消点赞）。目前笔记的内容主要是图文内容，后续可以支持在笔记中引用酒店、景点、行程等。

```
0.1.0版本暂时不需要实现笔记的管理员审核功能。
```
**组件内部细节**

实现语言：Java

具体效果可以参考马蜂窝（https://www.mafengwo.cn/index.php）的游记功能和知乎
（https://www.zhihu.com）的文章功能。马蜂窝的游记和知乎的文章都有一个类似的概念“头图/封面”，可以
来自笔记内的第一张图片，也可以让用户在编辑界面指定上传图片。

涉及的模型包括Note（和Draft？），以下是创建草稿、编辑草稿、发布笔记的泳道图：


#### 还有一个需要注意的点是图片资源的管理，也就是如何判断笔记更新后，旧的图片资源需要被如何移除。

由于前端会使用CherryMarkdown（https://github.com/Tencent/cherry-markdown）作为Markdown的渲染/编
辑器，因此需要注意适配CherryMarkdown所需的接口，具体请查阅CherryMarkdown的相关文档
（https://github.com/Tencent/cherry-markdown/wiki/），并和前端开发的同学协商清楚。

用户写的笔记可以如何被索引并被为其他Agent提供参考信息？

ES（异步）

**组件外部属性**

- gRPC^

需要提供创建草稿、发布草稿、复制草稿、上传图片、加载（笔记/草稿）内容、保存草稿，用户查看笔记列
表、删除笔记、查看（对应）草稿、删除草稿等基本的功能，然后还需要支持笔记点赞/取消点赞。

- MCP^

可能需要对应地将一些常用的工具封装为MCP工具。（TODO）

### 笔记创作（trip-note-creator）[ 顾若楠 , 谢森煜 ]

**Overview**

笔记创作（trip-note-creator）Agent，主要在发布笔记和编辑笔记时进行辅助创作，可以参考知乎创作中心
的“创作助手”，例如可以生成标题、总结导语、智能排版、智能大纲、文案精化等。


#### 组件内部细节

实现语言：Python

使用AutoGen框架实现的简易的笔记创作助手，内部在使用AutoGen实现的时候可以分成好几个小Agent，然
后由一个调度器统一调度，最好要覆盖ReAct和Reflexion等模式。

#### 尽量在后续的版本中可以添加多模态的支持。


#### 组件外部属性

- gRPC^

提供接口支持一些固定的工作流，包括但不限于：智能生成标题、智能识别错别字、智能总结导语等等。

- AgentCard^

支持A2A协议直接通讯，提供NL驱动的文本内容创作，类似Vibe Coding那种感觉，简单点嵌入一个聊天窗

```
CodeX、Copilot那种太复杂了不要
```
### Web前端（trip-web-frontend）[ 瘦头陀阿迪 325 , 谢森煜 ]

**Overview**

用Nuxt.js实现的dual-layered前端服务，参考OpenTelemetry Demo
（https://opentelemetry.io/docs/demo/architecture/）中的"Frontend"服务，同时渲染页面和提供RESTful
API。大部分RESTful API通过对系统内部的gRPC API进行封装而来。

**组件内部细节**

实现语言：TypeScript（Node.js）

使用Nust.js框架实现的Web前端。

前端在笔记草稿编辑界面需要嵌入一个Markdown渲染/编辑器。

为了支持智能行程规划，前端行程规划的Page/View需要对应维护一个Ephemeral Itinerary Model作为状态。

```
目前可以先实现的组件/页面：
1 .评论区组件
2 .笔记草稿编辑页面：基于CherryMarkdown
3 .登陆注册页面
4 .聊天组件（首页/行程规划/写作助手都要用）：样式上可以参考ChatGPT、OpenWebUI、Gemini
5 .行程智能规划页面
```
**组件外部属性**

- RESTful API^

主要是封装微服务系统内部的gRPC API将其转为RESTful API。当然也有部分微服务直接提供RESTful API，例
如聊天服务（trip-chat-service）。

### 文件服务（trip-file-service）[ 李展发 ]

**Overview**

我们提供一个单独的文件服务，用于管理文件（主要是点评、酒店等的图片）。

文档参考： 文件服务技术方案

**组件内部细节**

实现语言：Golang


Object Storage：MinIO

SDK：https://github.com/minio/minio-go

## 基础设施/中间件

### API网关

Higress

JWT Token鉴权，并在HTTP请求头中携带上从JWT Token里解析出来的User ID（以"X-User-Id"作为键），从
网关到Nuxt App（trip-web-frontend）仍然是直接HTTP协议，后续在Nuxt App中被转换为gRPC调用，gRPC
Client在Metadata中携带上User ID（以"user-id"为键）。

### AI网关

Higress

系统内部向外部MaaS或Self-hosted MaaS进行请求的出口代理网关。

### 服务注册与发现

Nacos

### 可观测性组件（observability）[ 顾若楠 ]

#### 云原生可观测性+大模型可观测性

需要部署一个开源的大模型/Agent可观测平台，比如 langfuse？Grafana 看各种指标各种 Agent的Trace

### 消息队列

RocketMQ

### 数据库

关系型数据库：MySQL

非关系型数据库：MongoDB（文档数据库）、Redis（内存数据库）、Milvus（向量数据库）

## 核心业务流程

## 组件间关系

### 基于聊天服务的对话管理


## 技术细节

### 技术栈说明

开发语言：Java（≥17）、Go（≥1.20）、Python（3.12）、TypeScript（Node.js）

SQL数据库：MySQL

NoSQL数据库：MongoDB、Redis

对象存储：MinIO

RPC框架：gRPC

API网关：Higress

服务注册与发现：Nacos（2.5.1）

可观测性：OpenTelemetry、Prometheus、Loki、Tempo、Grafana

LLM可观测性：

开发框架：Spring Boot（3.2.4）、Nuxt.js


### 全局实现约定

#### 1 .数据库主键

关系型数据库（如MySQL）统一使用UUID7作为主键，然后以binary的类型存在数据库中，例如在MySQL中可
以是BINARY(16)类型。

MongoDB的文档主键（_id）可以直接使用默认生成的ObjectId，如果要用自己生成的就也用UUID7。

```
2 .服务间通信
```
内部服务之间使用gRPC，对外提供HTTP API。具体来说，目前0.1.0版本的架构采用Nuxt.js框架，同时构建
Client Side App和RESTful API layer，然后在Nuxt.js App中实现API组合模式（主要是行程的查询视图）和
gRPC<->REST API的转换。可以参考OpenTelemetry Demo的架构图
（https://opentelemetry.io/docs/demo/architecture/）中的"Frontend"：


#### 后续在0.2.0或0.3.0版本可以考虑引入CQRS模式来代替API组合模式。

```
3 .A2A Task/Message UUID
```
在生成A2A中Task或Message时，统一使用UUID7来生成其ID，UUID生成后转为字符串。Message的ID是由
Sender生成的，Task的ID是由Server生成的。请大家在开发Agent之前务必熟悉A2A协议（https://a2a-
protocol.org/dev/），并过一遍A2A协议通讯的一般（Client/Server）工作流程、Task的声明周期等。

```
4 .图片存储
```
目前0.1.0版本我们暂时不搞trip-file-service这种微服务（？），因为目前主要涉及到的文件就只有图片，各个
微服务/Agent自行管理图片即可。图片的存储使用MinIO，各服务自己保存文件名、URL、归属的桶等等信
息。

我们在0.1.0版本是否真的需要搞一个trip-file-service？ 李展发

在0.2.0或0.3.0版本可以考虑将各个服务中的文件管理业务独立到一个统一的文件服务（trip-file-service）
里。


