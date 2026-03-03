"use client";

import Markdown from "react-markdown";
import type { Itinerary } from "@/actions/itinerary";

interface ItineraryViewerProps {
  itinerary: Itinerary;
  markdownContent: string;
}

export function ItineraryViewer({
  itinerary,
  markdownContent,
}: ItineraryViewerProps) {
  if (!markdownContent && itinerary.day_plans.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        暂无行程内容
      </div>
    );
  }

  if (markdownContent) {
    return (
      <div className="h-full overflow-y-auto">
        <article className="prose prose-blue max-w-none px-6 py-4">
          <Markdown>{markdownContent}</Markdown>
        </article>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <h1 className="mb-4 text-2xl font-bold text-gray-900">
        {itinerary.destination} 旅行计划
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        {itinerary.start_date} ~ {itinerary.end_date}
      </p>

      <div className="flex flex-col gap-6">
        {itinerary.day_plans.map((day) => (
          <section key={day.day_number} className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold text-gray-800">
              第{day.day_number}天
              <span className="ml-2 text-sm font-normal text-gray-400">
                {day.date}
              </span>
            </h2>

            <div className="flex flex-col gap-2 border-l-2 border-blue-200 pl-4">
              {day.activities.map((activity) => (
                <div
                  key={activity.id}
                  className="relative rounded-lg border border-gray-100 bg-white p-3 shadow-xs"
                >
                  <div className="absolute -left-[1.3rem] top-3.5 size-2.5 rounded-full bg-blue-500" />
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-blue-600">
                          {activity.start_time} - {activity.end_time}
                        </span>
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                          {activity.category}
                        </span>
                      </div>
                      <h3 className="mt-1 font-medium text-gray-900">
                        {activity.name}
                      </h3>
                      {activity.description && (
                        <p className="mt-0.5 text-sm text-gray-500">
                          {activity.description}
                        </p>
                      )}
                    </div>
                    {activity.estimated_cost.amount > 0 && (
                      <span className="shrink-0 text-sm font-medium text-orange-500">
                        ¥{activity.estimated_cost.amount}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {day.notes && (
              <p className="text-xs text-gray-400 italic">{day.notes}</p>
            )}
          </section>
        ))}
      </div>

      {itinerary.summary && (
        <div className="mt-8 rounded-lg bg-blue-50 p-4">
          <h3 className="font-medium text-blue-800">行程总结</h3>
          <div className="mt-2 flex gap-6 text-sm text-blue-700">
            <span>
              共 {itinerary.summary.total_activities} 个活动
            </span>
            <span>
              预估总费用 ¥{itinerary.summary.total_estimated_cost}
            </span>
          </div>
          {itinerary.summary.highlights.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-2">
              {itinerary.summary.highlights.map((h, i) => (
                <li
                  key={i}
                  className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs text-blue-700"
                >
                  {h}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
