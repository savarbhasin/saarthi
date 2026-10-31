import { Customise } from "./sections/Customise";
import { Evening } from "./sections/Evening";
import { Finale } from "./sections/Finale";
import { Hero } from "./sections/Hero";
import { HowItWorks } from "./sections/HowItWorks";
import { LiveTasks } from "./sections/LiveTasks";
import { Nav } from "./sections/Nav";
import { Phrases } from "./sections/Phrases";
import { Work } from "./sections/Work";

export function Landing() {
  return (
    <div className="overflow-x-clip">
      <Nav />
      <main>
        <Hero />
        <HowItWorks />
        <LiveTasks />
        <Work />
        <Evening />
        <Customise />
        <Phrases />
        <Finale />
      </main>
    </div>
  );
}
