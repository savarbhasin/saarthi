import { api, type Routine } from "../api";
import { Button, Card, Empty, Hero, Loading, Notice } from "../components/ui";
import { useLoad } from "../useLoad";

export function Schedule() {
  const { data: routines, error, reload } = useLoad<Routine[]>("/schedule");
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!routines) return <Loading />;

  async function stop(routine: Routine) {
    if (!confirm("Stop this?")) return;
    await api(`/schedule/${routine.id}`, "DELETE");
    await reload();
  }

  return (
    <>
      <Hero
        icon="calendar"
        title="Schedule"
        lede="Reminders and jobs Saarthi will run for you. To add one, just ask on a call."
      />
      {routines.map((routine) => (
        <Card key={routine.id}>
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0 flex-1">{routine.text}</div>
            <Button small variant="danger" onClick={() => stop(routine)}>
              Stop
            </Button>
          </div>
        </Card>
      ))}
      {routines.length === 0 && (
        <Empty icon="calendar" title="Nothing scheduled">
          Try saying "हर सुबह 7 बजे मंडी का भाव बताना".
        </Empty>
      )}
    </>
  );
}
