import { Timeline, Label } from "@primer/react";
import {
  GearIcon,
  CommentIcon,
  InfoIcon,
  AlertIcon,
} from "@primer/octicons-react";
import type { AssessEvent } from "../api/types";

function eventIcon(event: AssessEvent): React.ReactElement {
  switch (event.type) {
    case "tool":
      return (
        <Timeline.Badge>
          <GearIcon />
        </Timeline.Badge>
      );
    case "reasoning":
      return (
        <Timeline.Badge>
          <CommentIcon />
        </Timeline.Badge>
      );
    case "status":
      return (
        <Timeline.Badge>
          <InfoIcon />
        </Timeline.Badge>
      );
    case "error":
      return (
        <Timeline.Badge className="event-badge-danger">
          <AlertIcon />
        </Timeline.Badge>
      );
    default:
      return (
        <Timeline.Badge>
          <InfoIcon />
        </Timeline.Badge>
      );
  }
}

function eventContent(event: AssessEvent): React.ReactElement {
  switch (event.type) {
    case "tool":
      return (
        <span className="event-line">
          <Label variant="accent" className="event-label event-label--tool">
            tool
          </Label>
          <code className="event-tool-name">{event.tool}</code>
          {event.detail && (
            <span className="event-detail">{event.detail}</span>
          )}
        </span>
      );
    case "reasoning":
      return (
        <span className="event-line">
          <Label variant="secondary" className="event-label event-label--thinking">
            thinking
          </Label>
          <span className="event-reasoning">{event.message}</span>
        </span>
      );
    case "status":
      return (
        <span className="event-line">
          <Label className="event-label event-label--status">status</Label>
          <span>{event.message}</span>
        </span>
      );
    case "error":
      return (
        <span className="event-line">
          <Label variant="danger" className="event-label event-label--error">
            error
          </Label>
          <span className="event-error">{event.message}</span>
        </span>
      );
    default:
      return <span>Unknown event</span>;
  }
}

interface EventLogProps {
  events: AssessEvent[];
}

export function EventLog({ events }: EventLogProps): React.ReactElement {
  return (
    <div className="event-log">
      {events.length === 0 ? (
        <span className="event-waiting">Waiting for events\u2026</span>
      ) : (
        <Timeline>
          {events.map((event, i) => (
            <Timeline.Item key={i} condensed>
              {eventIcon(event)}
              <Timeline.Body>{eventContent(event)}</Timeline.Body>
            </Timeline.Item>
          ))}
        </Timeline>
      )}
    </div>
  );
}
