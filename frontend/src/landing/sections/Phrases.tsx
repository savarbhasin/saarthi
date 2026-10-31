import { InfiniteMovingCards } from "../ui/infinite-moving-cards";
import { Heading } from "./Section";

// Phrases from the web app's guide; the tag says which profile or ability each one is from.
const ROW_ONE: [string, string][] = [
  ["आज सोने का भाव क्या है", "Answers"],
  ["दिल्ली से जयपुर की कल की ट्रेनें देखो", "Research"],
  ["कल सुबह 7 बजे दवाई याद दिलाना", "Reminders"],
  ["मेरे भाई को फ़ोन करके बोलो मैं शाम को आऊँगा", "Calls"],
  ["याद रखना मेरी बेटी का नाम प्रिया है", "Memory"],
  ["Can we talk in English?", "Languages"],
  ["Redmi Note 14 का सबसे सस्ता दाम ढूँढो", "Research"],
  ["हर रविवार सुबह मौसम बताना", "Routines"],
];

const ROW_TWO: [string, string][] = [
  ["सबसे ज़्यादा उधार किस पर है", "Kirana"],
  ["अगले हफ्ते बारिश होगी क्या", "Farmer"],
  ["इस हफ्ते कितना कमाया", "Driver"],
  ["कल का काम बताओ", "Tradesperson"],
  ["आज बीपी 140 पर 90 आया", "Elder care"],
  ["पीएम किसान की किस्त कब आएगी", "Farmer"],
  ["தமிழில் பேசலாமா?", "Languages"],
  ["ऑर्डर लिस्ट पढ़कर सुनाओ", "Kirana"],
];

const card = ([say, tag]: [string, string]) => ({
  key: say,
  node: (
    <div className="flex w-[300px] flex-col gap-3 border border-line bg-surface px-5 py-4 md:w-[360px]">
      <span className="font-mono text-[11px] font-semibold tracking-wider text-accent uppercase">{tag}</span>
      <span className="text-lg leading-snug font-semibold">“{say}”</span>
    </div>
  ),
});

export function Phrases() {
  return (
    // The marquee runs edge to edge, so this section skips the usual centred column.
    <section className="border-t border-line bg-surface py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-4 md:px-10 xl:px-0">
        <Heading title="Talk to it like you'd talk to a friend." />
      </div>
      <div className="mt-12 grid gap-3">
        <InfiniteMovingCards items={ROW_ONE.map(card)} speed={70} />
        <InfiniteMovingCards items={ROW_TWO.map(card)} speed={80} direction="right" />
      </div>
    </section>
  );
}
