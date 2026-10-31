import { Link } from "react-router-dom";
import type { Ability, Guide as GuideData } from "../api";
import { Icon } from "../components/Icon";
import { Hero, Loading, Notice, SectionLabel } from "../components/ui";
import { useLoad } from "../useLoad";

function AbilityCard({ ability }: { ability: Ability }) {
  return (
    <article className="flex flex-col border border-line bg-surface px-5 py-4.5">
      <h3 className="text-[17px] font-bold">{ability.title}</h3>
      <p className="mt-1 text-[15px] leading-relaxed text-muted">{ability.detail}</p>
      <div className="mt-auto pt-4">
        <div className="mb-1.5 text-xs font-semibold tracking-[0.08em] text-muted uppercase">Say</div>
        <ul className="grid gap-1.5">
          {ability.examples.map((example) => (
            <li key={example} className="flex items-start gap-2 bg-canvas px-3 py-2 text-[15px]">
              <span className="mt-0.5 text-accent">
                <Icon name="phone" className="size-4" />
              </span>
              “{example}”
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

export function Guide() {
  const { data: guide, error } = useLoad<GuideData>("/guide");
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!guide) return <Loading />;

  return (
    <>
      <Hero icon="bolt" title="What Saarthi can do" lede="Call Saarthi and just say it, in your own words and language." />

      {guide.profile.length > 0 ? (
        <>
          <SectionLabel>For your work · {guide.pack_label}</SectionLabel>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {guide.profile.map((ability) => (
              <AbilityCard key={ability.title} ability={ability} />
            ))}
          </div>
        </>
      ) : (
        <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 bg-accent-soft px-4 py-3 text-[15px]">
          <span>
            Saarthi knows extra for shopkeepers, farmers, drivers, tradespeople and more. Tell it what you do to
            unlock that.
          </span>
          <Link to="/you" className="font-semibold text-accent">
            Pick your profile →
          </Link>
        </div>
      )}

      <SectionLabel>For everyone</SectionLabel>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {guide.everyone.map((ability) => (
          <AbilityCard key={ability.title} ability={ability} />
        ))}
      </div>
    </>
  );
}
