import { UnderlineNav } from "@primer/react";
import { BeakerIcon, ZapIcon } from "@primer/octicons-react";
import { useLocation, useNavigate } from "react-router";

export function AppHeader(): React.ReactElement {
  const location = useLocation();
  const navigate = useNavigate();
  const current = location.pathname;

  return (
    <>
      <header className="app-header">
        <a
          href="/"
          onClick={(e: React.MouseEvent) => {
            e.preventDefault();
            navigate("/assess");
          }}
          className="app-header-brand"
        >
          HVE Stem
        </a>
      </header>
      <div className="underline-nav-container">
        <UnderlineNav aria-label="Main navigation">
          <UnderlineNav.Item
            aria-current={current === "/assess" ? "page" : undefined}
            onSelect={(e) => {
              e.preventDefault();
              navigate("/assess");
            }}
            leadingVisual={<BeakerIcon />}
          >
            Assess
          </UnderlineNav.Item>
          <UnderlineNav.Item
            aria-current={current === "/remediate" ? "page" : undefined}
            onSelect={(e) => {
              e.preventDefault();
              navigate("/remediate");
            }}
            leadingVisual={<ZapIcon />}
          >
            Remediate
          </UnderlineNav.Item>
        </UnderlineNav>
      </div>
    </>
  );
}
