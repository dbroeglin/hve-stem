import { Heading, Text, Button } from "@primer/react";
import { ZapIcon, TerminalIcon } from "@primer/octicons-react";

export function RemediatePage(): React.ReactElement {
  return (
    <div>
      <div className="page-header-section">
        <Heading as="h2" className="page-title">
          Remediation
        </Heading>
        <Text as="p" className="page-description">
          Read assessment findings and create GitHub issues on the target
          repository for each finding, with contextual fix suggestions.
        </Text>
      </div>

      <div className="blankslate">
        <ZapIcon size={48} className="blankslate-icon" />
        <Heading as="h3" className="blankslate-heading">
          Remediation is not yet available in the web UI
        </Heading>
        <Text as="p" className="blankslate-description">
          You can run remediation from the command line to create GitHub issues
          for assessment findings with contextual fix suggestions.
        </Text>
        <div className="blankslate-action">
          <Button
            as="a"
            href="https://github.com/dbroeglin/hve-stem#remediation"
            target="_blank"
            rel="noopener noreferrer"
            leadingVisual={TerminalIcon}
          >
            <code>stem remediate</code>
          </Button>
        </div>
      </div>
    </div>
  );
}
