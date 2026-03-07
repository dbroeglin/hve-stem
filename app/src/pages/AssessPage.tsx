import { useState, useRef, useEffect } from "react";
import {
  Button,
  Flash,
  Spinner,
  Text,
  Heading,
  FormControl,
  StateLabel,
  ActionMenu,
  ActionList,
  IconButton,
} from "@primer/react";
import { ChevronDownIcon, ChevronRightIcon } from "@primer/octicons-react";
import { BeakerIcon, RepoIcon } from "@primer/octicons-react";
import { fetchTargets } from "../api/client";
import { useAssess } from "../api/useAssess";
import { EventLog } from "../components/EventLog";
import { MarkdownReport } from "../components/MarkdownReport";

export function AssessPage(): React.ReactElement {
  const [targets, setTargets] = useState<string[]>([]);
  const [repo, setRepo] = useState("");
  const [targetsError, setTargetsError] = useState<string | null>(null);
  const { events, result, isRunning, error, run } = useAssess();
  const logEndRef = useRef<HTMLDivElement>(null);
  const [logOpen, setLogOpen] = useState(true);

  useEffect(() => {
    fetchTargets()
      .then((repos) => {
        setTargets(repos);
        if (repos.length > 0) {
          setRepo(repos[0]);
        }
      })
      .catch((err: Error) => setTargetsError(err.message));
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (repo.trim() && !isRunning) {
      run(repo.trim());
    }
  };

  return (
    <div>
      <div className="page-header-section">
        <div className="page-header-row">
          <Heading as="h2" className="page-title">
            Assessment
          </Heading>
          {isRunning && (
            <StateLabel status="issueOpened">Running</StateLabel>
          )}
        </div>
        <Text as="p" className="page-description">
          Evaluate a GitHub repository against the desired SDLC blueprint. The
          assessment will check delivery performance, code health, collaboration,
          agentic maturity, and governance compliance.
        </Text>
      </div>

      {targetsError && (
        <Flash variant="danger" className="flash-message">
          Failed to load targets: {targetsError}
        </Flash>
      )}

      <div className="gh-box">
        <div className="gh-box-header">
          <Heading as="h3" className="gh-box-title">
            <RepoIcon size={16} />
            Target repository
          </Heading>
        </div>
        <div className="gh-box-body">
          <form onSubmit={handleSubmit} className="assess-form">
            <FormControl className="assess-form__input">
              <FormControl.Label>Repository</FormControl.Label>
              {targets.length > 0 ? (
                <ActionMenu>
                  <ActionMenu.Button
                    disabled={isRunning}
                    leadingVisual={RepoIcon}
                  >
                    {repo || "Select a repository"}
                  </ActionMenu.Button>
                  <ActionMenu.Overlay>
                    <ActionList selectionVariant="single">
                      {targets.map((t) => (
                        <ActionList.Item
                          key={t}
                          selected={t === repo}
                          onSelect={() => setRepo(t)}
                        >
                          {t}
                        </ActionList.Item>
                      ))}
                    </ActionList>
                  </ActionMenu.Overlay>
                </ActionMenu>
              ) : (
                <Text as="p" className="text-muted">
                  No targets configured in stem.yaml
                </Text>
              )}
            </FormControl>
            <Button
              type="submit"
              variant="primary"
              size="large"
              disabled={!repo.trim()}
              loading={isRunning}
              leadingVisual={BeakerIcon}
              className="assess-form__submit"
            >
              {isRunning ? "Running\u2026" : "Run Assessment"}
            </Button>
          </form>
        </div>
      </div>

      {error && (
        <Flash variant="danger" className="flash-message">
          {error}
        </Flash>
      )}

      {(events.length > 0 || isRunning) && (
        <div className="gh-box">
          <div
            className="gh-box-header gh-box-header--clickable"
            onClick={() => setLogOpen((prev) => !prev)}
          >
            <Heading as="h3" className="gh-box-title">
              <IconButton
                aria-label={logOpen ? "Collapse event log" : "Expand event log"}
                icon={logOpen ? ChevronDownIcon : ChevronRightIcon}
                variant="invisible"
                size="small"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  setLogOpen((prev) => !prev);
                }}
              />
              {isRunning ? (
                <span className="gh-box-title-with-status">
                  <Spinner size="small" />
                  Assessment in progress…
                </span>
              ) : (
                "Event Log"
              )}
            </Heading>
          </div>
          {logOpen && (
            <div className="gh-box-body gh-box-body--log">
              <EventLog events={events} />
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="gh-box">
          <div className="gh-box-header">
            <Heading as="h3" className="gh-box-title">
              Assessment Report
            </Heading>
          </div>
          <div className="gh-box-body gh-box-body--report">
            <MarkdownReport content={result} />
          </div>
        </div>
      )}
    </div>
  );
}
