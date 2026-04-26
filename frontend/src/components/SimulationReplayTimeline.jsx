import React from "react";
import { Clock, Sparkles } from "lucide-react";

const summarizeRound = (roundPosts) => {
  const real = roundPosts.filter((post) => post.is_real).length;
  const reactions = roundPosts.filter((post) => post.post_type === "reaction").length;
  const viral = roundPosts.filter((post) => post.viral).length;
  const injected = roundPosts.find((post) => post.injected_variable)?.injected_variable;

  if (injected) return `Injected event response: ${injected}`;
  if (real) return `${real} real-world seed posts anchored the simulation.`;
  if (reactions) return `${reactions} agents reacted to a new variable.`;
  if (viral) return `${viral} viral post(s) shaped the feed.`;
  return `${roundPosts.length} simulated posts and replies generated.`;
};

const SimulationReplayTimeline = ({ posts = [], narratives = [] }) => {
  if (!posts.length) return null;

  const rounds = Object.values(
    posts.reduce((acc, post) => {
      const round = post.round ?? 0;
      acc[round] = acc[round] || { round, posts: [] };
      acc[round].posts.push(post);
      return acc;
    }, {})
  ).sort((a, b) => a.round - b.round);

  return (
    <div data-testid="simulation-replay-timeline" className="bg-panel border border-sw rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-4 h-4 text-sw-cyan" />
        <h3 className="text-sm font-bold text-sw">Simulation Replay Timeline</h3>
      </div>
      <div className="space-y-3">
        {rounds.map(({ round, posts: roundPosts }) => {
          const narrative = round > 0 ? narratives[round - 1] : null;
          const sample = roundPosts[0];
          return (
            <div key={round} className="relative pl-6">
              <div className="absolute left-0 top-1 w-3 h-3 rounded-full bg-sw-cyan shadow-[0_0_12px_rgba(0,245,196,0.45)]" />
              <div className="absolute left-[5px] top-5 bottom-[-14px] w-px bg-sw" />
              <div className="rounded-lg bg-sw3/40 border border-sw p-3">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-xs font-semibold text-sw-cyan mono">Round {round}</span>
                  <span className="text-[10px] text-sw3">{roundPosts.length} posts</span>
                </div>
                <p className="text-xs text-sw2">{narrative || summarizeRound(roundPosts)}</p>
                {sample && (
                  <div className="mt-2 flex items-start gap-2 text-[11px] text-sw3">
                    <Sparkles className="w-3 h-3 mt-0.5 text-amber-400 flex-shrink-0" />
                    <span>{sample.agent_name}: {sample.content?.slice(0, 120)}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SimulationReplayTimeline;
