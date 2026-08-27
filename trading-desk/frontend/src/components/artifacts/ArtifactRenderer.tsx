import { RecommendationCard } from './RecommendationCard';
import { ExposureSummaryCard } from './ExposureSummaryCard';
import type { Recommendation } from '@/types';

interface Artifact {
  type: string;
  data: Record<string, unknown>;
}

interface ArtifactRendererProps {
  artifacts: Artifact[];
}

export function ArtifactRenderer({ artifacts }: ArtifactRendererProps) {
  return (
    <>
      {artifacts.map((art, i) => {
        switch (art.type) {
          case 'recommendation_card':
            return (
              <RecommendationCard
                key={i}
                data={art.data as unknown as Recommendation & { id: string }}
                compact
              />
            );
          case 'exposure_summary':
            return <ExposureSummaryCard key={i} data={art.data} />;
          case 'bot_rationale':
            return (
              <div key={i} className="mt-2 rounded-lg border border-gray-700 bg-surface-overlay p-3 text-sm">
                <span className="text-xs font-semibold text-gray-400">Bot Rationale</span>
                <p className="mt-1 whitespace-pre-wrap">{(art.data as { rationale?: string }).rationale}</p>
              </div>
            );
          default:
            return null;
        }
      })}
    </>
  );
}
