import React from "react";
import { Loader2 } from "lucide-react";

const SimulationFeed = ({ title, icon, posts, feedRef, isDone, emptyLabel, renderPost }) => (
  <div className="flex flex-col h-[500px] border border-sw rounded-xl bg-panel overflow-hidden">
    <div className="px-3 py-2 border-b border-sw flex items-center justify-between bg-sw-bg2">
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-semibold text-sw text-sm">{title}</span>
      </div>
      <span className="text-[10px] text-sw3">{posts.length} posts</span>
    </div>
    <div ref={feedRef} className="flex-1 overflow-y-auto p-3 space-y-2">
      {posts.map((post, index) => renderPost(post, index))}
      {!isDone && posts.length === 0 && (
        <div className="flex items-center justify-center h-full text-sw3 text-sm">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          {emptyLabel || "Waiting for posts..."}
        </div>
      )}
    </div>
  </div>
);

export default SimulationFeed;
