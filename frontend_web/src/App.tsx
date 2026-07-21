import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent } from "react";

type Palette = Record<string, string>;
type ThemeOption = { name: string; label?: string; swatchA?: string; swatchB?: string };
type AgentOption = { name: string; owned?: boolean; icon?: string };
type MapOption = { uuid: string; name: string };
type Friend = { puuid: string; display_name?: string; game_name?: string; game_tag?: string };
type Weapon = { weapon?: string; weaponName?: string; skinId?: string; skinName?: string; skinIcon?: string; buddyIcon?: string; icon?: string; iconPath?: string };
type PlayerCard = {
  puuid?: string;
  displayName?: string;
  name?: string;
  tag?: string;
  tagLine?: string;
  playerKey?: string;
  clipboardName?: string;
  agentName?: string;
  agentIcon?: string;
  agentIconPath?: string;
  levelText?: string;
  rankIcon?: string;
  rankIconPath?: string;
  rankText?: string;
  rrText?: string;
  rrValue?: number;
  rrMax?: number;
  peakRankIcon?: string;
  peakRankIconPath?: string;
  peakRankText?: string;
  peakActText?: string;
  recentRrChanges?: { valueText?: string; text?: string; numericValue?: number; tone?: string }[];
  weapons?: Weapon[];
  weaponIcons?: Weapon[];
  stats?: Record<string, { label?: string; value?: string; tone?: string }>;
  trackerUrl?: string;
  vtlUrl?: string;
  isFlagged?: boolean;
  flagTooltip?: string;
  copyIconPath?: string;
  vtlIconPath?: string;
  flagIconPath?: string;
  playerIconPath?: string;
  playerIconTooltip?: string;
  buddyIconPath?: string;
};

type Snapshot = {
  appTitle?: string;
  status?: { message?: string; loading?: boolean; progress?: { loaded?: number; total?: number } };
  theme?: { name?: string; surfaceMode?: string; palette?: Palette; options?: ThemeOption[]; surfaceModes?: string[] };
  themePalette?: Palette;
  header?: { gamemode?: string; server?: string; startingSideText?: string; canRefresh?: boolean; canDodge?: boolean; canLoadMore?: boolean };
  agentLock?: { selectedAgent?: string; standardAgent?: string; autoLockEnabled?: boolean; mapSpecificEnabled?: boolean; mapSpecificAvailable?: boolean; options?: AgentOption[] };
  mapAgents?: { maps?: MapOption[]; selection?: Record<string, string>; agentOptions?: AgentOption[] };
  queueSnipe?: { enabled?: boolean; available?: boolean; selectedFriend?: Friend | null; friends?: Friend[]; loading?: boolean; error?: string };
  presence?: { mode?: string; available?: boolean };
  tools?: { partyDetectionEnabled?: boolean; queueSnipeEnabled?: boolean; presenceMode?: string };
  leftPlayers?: PlayerCard[];
  rightPlayers?: PlayerCard[];
  ownedLoadoutEditor?: { loading?: boolean; weapons?: Weapon[]; presets?: string[]; selectedPreset?: string };
  playerLoadouts?: { playerName?: string; weapons?: Weapon[] } | null;
  activeModal?: string | null;
  modalData?: Record<string, unknown>;
  validationErrors?: string[];
  toast?: { message?: string; tone?: string } | null;
  prompts?: { restart?: Record<string, string> | null; update?: Record<string, string> | null };
};

type QtBridge = {
  getSnapshot: (callback: (snapshotJson: string) => void) => void;
  dispatch?: (actionJson: string, callback?: (resultJson: string) => void) => void;
  openTracker?: (url: string) => void;
  openVtl?: (url: string) => void;
  copyText?: (text: string) => void;
  startWindowMove?: () => void;
  maximizeWindow?: () => void;
  toggleMaximizeRestore?: () => void;
  minimizeWindow?: () => void;
  closeWindow?: () => void;
  snapshotChanged?: { connect: (callback: (snapshotJson: string) => void) => void };
};

declare global {
  interface Window {
    qt?: { webChannelTransport: unknown };
    QWebChannel?: new (transport: unknown, callback: (channel: { objects: { valScannerBridge: QtBridge } }) => void) => void;
  }
}

const fallbackSnapshot: Snapshot = {
  appTitle: "ValScanner",
  status: { message: "Mock data", loading: false, progress: { loaded: 0, total: 0 } },
  theme: {
    name: "midnight",
    surfaceMode: "opaque",
    palette: {
      main: "#121a25",
      window: "#0d141d",
      panel: "#111b27",
      card: "#162232",
      cardAlt: "#1b2a3d",
      border: "#2a3b50",
      borderSoft: "#223247",
      text: "#e6edf7",
      muted: "#96a6b9",
      accent: "#6aa6e8",
      accentHover: "#78b2f0",
      teal: "#64c7ad",
      red: "#c9606b",
      gold: "#d9af68",
      cyan: "#8bd6e8"
    },
    options: [],
    surfaceModes: ["transparent", "opaque"]
  },
  header: { gamemode: "Unknown", server: "Unknown", startingSideText: "", canRefresh: true, canDodge: false, canLoadMore: false },
  agentLock: { selectedAgent: "Random", standardAgent: "Random", autoLockEnabled: false, mapSpecificEnabled: false, mapSpecificAvailable: false, options: [{ name: "Random" }] },
  mapAgents: { maps: [], selection: {}, agentOptions: [] },
  queueSnipe: { enabled: false, available: false, selectedFriend: null, friends: [], loading: false, error: "" },
  presence: { mode: "online", available: true },
  tools: { partyDetectionEnabled: false, queueSnipeEnabled: false, presenceMode: "online" },
  leftPlayers: [],
  rightPlayers: [],
  ownedLoadoutEditor: { loading: false, weapons: [], presets: [], selectedPreset: "" },
  activeModal: null
};

function parseSnapshot(snapshotJson: string): Snapshot {
  try {
    return { ...fallbackSnapshot, ...(JSON.parse(snapshotJson) as Snapshot) };
  } catch {
    return fallbackSnapshot;
  }
}

function loadQWebChannelScript() {
  return new Promise<void>((resolve, reject) => {
    if (window.QWebChannel) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = "qrc:///qtwebchannel/qwebchannel.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("qwebchannel.js failed to load"));
    document.head.appendChild(script);
  });
}

function dash(value?: string | number) {
  const text = String(value ?? "").trim();
  return text && text !== "[]" ? text : "-";
}

function normalizeTag(tag?: string, tagLine?: string) {
  return String(tagLine || tag || "").trim().replace(/^#/, "");
}

function playerDisplayParts(player: PlayerCard) {
  const tag = normalizeTag(player.tag, player.tagLine);
  let displayName = dash(player.displayName || player.name);
  if (tag && displayName.toLowerCase().endsWith(`#${tag.toLowerCase()}`)) {
    displayName = displayName.slice(0, displayName.length - tag.length - 1);
  }
  return { displayName, tag };
}

function rrTone(change: { numericValue?: number; tone?: string }) {
  const numeric = Number(change.numericValue || 0);
  if (change.tone === "positive" || numeric > 0) return "positive";
  if (change.tone === "negative" || numeric < 0) return "negative";
  return "neutral";
}

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot>(fallbackSnapshot);
  const [bridge, setBridge] = useState<QtBridge | null>(null);
  const [bridgeStatus, setBridgeStatus] = useState("mock");

  useEffect(() => {
    if (!window.qt?.webChannelTransport) {
      return;
    }
    loadQWebChannelScript()
      .then(() => {
        if (!window.QWebChannel || !window.qt?.webChannelTransport) {
          throw new Error("QWebChannel unavailable");
        }
        new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
          const nextBridge = channel.objects.valScannerBridge;
          setBridge(nextBridge);
          setBridgeStatus("connected");
          nextBridge.getSnapshot((snapshotJson) => setSnapshot(parseSnapshot(snapshotJson)));
          nextBridge.snapshotChanged?.connect((snapshotJson) => setSnapshot(parseSnapshot(snapshotJson)));
        });
      })
      .catch((error) => setBridgeStatus(error instanceof Error ? error.message : "bridge unavailable"));
  }, []);

  const palette = useMemo(() => snapshot.theme?.palette || snapshot.themePalette || fallbackSnapshot.theme?.palette || {}, [snapshot]);
  const dispatch = (command: string, payload: Record<string, unknown> = {}) => {
    bridge?.dispatch?.(JSON.stringify({ command, payload }));
  };

  return (
    <main className="app" style={cssVars(palette)}>
      <Header snapshot={snapshot} bridge={bridge} dispatch={dispatch} />
      <section className="board">
        <TeamColumn title="Red Team" players={snapshot.leftPlayers || []} bridge={bridge} dispatch={dispatch} />
        <TeamColumn title="Blue Team" players={snapshot.rightPlayers || []} bridge={bridge} dispatch={dispatch} />
      </section>
      <StatusBar snapshot={snapshot} bridgeStatus={bridgeStatus} />
      <ModalLayer snapshot={snapshot} dispatch={dispatch} />
      {snapshot.status?.loading ? <LoadingOverlay status={snapshot.status} /> : null}
      {snapshot.toast?.message ? <div className={`toast ${snapshot.toast.tone || "neutral"}`}>{snapshot.toast.message}</div> : null}
    </main>
  );
}

function cssVars(palette: Palette) {
  return {
    "--main": palette.main,
    "--window": palette.window,
    "--panel": palette.panel,
    "--card": palette.card,
    "--card-alt": palette.cardAlt || palette.card_alt,
    "--border": palette.border,
    "--border-soft": palette.borderSoft || palette.border_soft || palette.border,
    "--text": palette.text,
    "--muted": palette.muted,
    "--accent": palette.accent,
    "--accent-hover": palette.accentHover || palette.accent_hover || palette.accent,
    "--teal": palette.teal,
    "--gold": palette.gold,
    "--cyan": palette.cyan || palette.teal,
    "--red": palette.red || palette.accent,
    "--flagged-row": palette.flaggedRow || palette.flagged_row || palette.card,
    "--flagged-border": palette.flaggedBorder || palette.flagged_border || palette.accent
  } as React.CSSProperties;
}

function Header({ snapshot, bridge, dispatch }: { snapshot: Snapshot; bridge: QtBridge | null; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const header = snapshot.header || {};
  const agent = snapshot.agentLock || {};
  const queue = snapshot.queueSnipe || {};
  const presence = snapshot.presence || {};
  const dragStart = useRef<{ x: number; y: number; interactive: boolean } | null>(null);

  const isInteractiveTarget = (target: EventTarget | null) => {
    return target instanceof Element && Boolean(target.closest("button, input, select, textarea, a, [data-no-drag='true']"));
  };

  const beginTopBarDrag = (event: PointerEvent<HTMLElement>) => {
    if (event.button !== 0) return;
    dragStart.current = {
      x: event.clientX,
      y: event.clientY,
      interactive: isInteractiveTarget(event.target)
    };
  };

  const moveTopBarDrag = (event: PointerEvent<HTMLElement>) => {
    const start = dragStart.current;
    if (!start || start.interactive || (event.buttons & 1) === 0) return;

    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (dx * dx + dy * dy < 16) return;

    dragStart.current = null;
    if (event.screenY <= 2) {
      bridge?.maximizeWindow?.();
    } else {
      bridge?.startWindowMove?.();
    }
  };

  const endTopBarDrag = (event: PointerEvent<HTMLElement>) => {
    if (!dragStart.current?.interactive && event.screenY <= 2) {
      bridge?.maximizeWindow?.();
    }
    dragStart.current = null;
  };
  return (
    <header
      className="topbar"
      onPointerDown={beginTopBarDrag}
      onPointerMove={moveTopBarDrag}
      onPointerUp={endTopBarDrag}
      onPointerCancel={() => { dragStart.current = null; }}
      onDoubleClick={(event) => {
        if (!isInteractiveTarget(event.target)) bridge?.toggleMaximizeRestore?.();
      }}
    >
      <section className="topbarGroup identityGroup">
        <div className="brandMark">VS</div>
        <div className="metricPair">
          <span>Mode</span>
          <strong>{header.gamemode || "Unknown"}</strong>
        </div>
        <div className="metricPair">
          <span>Server</span>
          <strong>{header.server || "Unknown"}</strong>
        </div>
      </section>
      <section className="topbarGroup agentControls" data-no-drag="true">
        <span className="groupLabel">Agent</span>
        <button className="flatButton agentSelect" onClick={() => dispatch("openAgentPicker")}>{agent.selectedAgent || "Random"}</button>
        <button className="flatButton accentButton" onClick={() => dispatch("lockAgent")}>Lock Agent</button>
        <Toggle label="Auto" checked={Boolean(agent.autoLockEnabled)} onChange={(enabled) => dispatch("setAutoLock", { enabled })} />
        <Toggle label="Map" checked={Boolean(agent.mapSpecificEnabled)} disabled={!agent.mapSpecificAvailable} onChange={(enabled) => dispatch("setMapSpecific", { enabled })} />
      </section>
      <section className="topbarGroup matchControls" data-no-drag="true">
        <div className="side">{header.startingSideText || "Pending side"}</div>
        <button className="flatButton dangerButton" disabled={!header.canDodge} onClick={() => dispatch("dodge")}>Dodge</button>
        <button className="flatButton" disabled={!header.canLoadMore} onClick={() => dispatch("loadMore")}>Load More</button>
        <button className="flatButton" onClick={() => dispatch("openTools")}>Tools</button>
        <button className="flatButton queueButton" disabled={!queue.available && !queue.selectedFriend} onClick={() => dispatch("openQueueSnipe")}>{queue.selectedFriend?.display_name || "Queue Snipe"}</button>
        <button className="flatIcon" disabled={!presence.available} title={presence.mode === "offline" ? "Appear Offline" : "Online"} onClick={() => dispatch("setPresenceMode", { mode: presence.mode === "offline" ? "online" : "offline" })}>{presence.mode === "offline" ? "OFF" : "ON"}</button>
      <button className="iconOnly refresh" disabled={!header.canRefresh} title="Refresh" onClick={() => dispatch("refresh")}>↻</button>
      </section>

      <section className="topbarGroup windowControls" data-no-drag="true">
        <button className="windowButton" title="Minimize" onClick={() => bridge?.minimizeWindow?.()}>-</button>
        <button className="windowButton" title="Maximize or restore" onClick={() => bridge?.toggleMaximizeRestore?.()}>[]</button>
        <button className="windowButton close" title="Close" onClick={() => bridge?.closeWindow?.()}>x</button>
      </section>
    </header>
  );
}

function Toggle({ label, checked, disabled, onChange }: { label: string; checked: boolean; disabled?: boolean; onChange: (enabled: boolean) => void }) {
  return <button className={`toggle ${checked ? "on" : ""}`} disabled={disabled} onClick={() => onChange(!checked)}><i /> <span>{label}</span></button>;
}

function TeamColumn({ title, players, bridge, dispatch }: { title: string; players: PlayerCard[]; bridge: QtBridge | null; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  return (
    <section className="team">
      <div className="teamTitle"><h2>{title}</h2><span>{players.length}</span></div>
      <div className="playerList">
        {players.length ? players.map((player, index) => <PlayerRow key={`${player.puuid || player.displayName}-${index}`} player={player} bridge={bridge} dispatch={dispatch} />) : <div className="empty">Waiting for player data</div>}
      </div>
    </section>
  );
}

function PlayerRow({ player, bridge, dispatch }: { player: PlayerCard; bridge: QtBridge | null; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const { displayName, tag } = playerDisplayParts(player);
  const copyText = player.clipboardName || (tag && player.name ? `${player.name}#${tag}` : displayName);
  const loadoutKey = player.playerKey || player.puuid || copyText;
  const stats = Object.values(player.stats || {});
  const rrChanges = player.recentRrChanges || [];
  return (
    <article className={`playerRow ${player.isFlagged ? "flagged" : ""}`}>
      <div className="portraitWrap">
        <AssetImage className="agentPortrait" src={player.agentIcon || player.agentIconPath} alt={player.agentName || ""} fallback={dash(player.agentName)} />
        <span className="levelBadge">{dash(player.levelText)}</span>
      </div>
      <div className="playerMain">
        <div className="nameLine">
          <button className="nameButton" onClick={() => player.trackerUrl && bridge?.openTracker?.(player.trackerUrl)}>{displayName}{tag ? <small>#{tag}</small> : null}</button>
          <InlineIcon src={player.playerIconPath} title={player.playerIconTooltip} />
          <InlineIcon src={player.buddyIconPath} title="Riot gun buddy equipped" />
          <IconButton label="Copy name" icon={player.copyIconPath} fallback="C" onClick={() => bridge?.copyText?.(copyText)} />
          <IconButton label="Open VTL" icon={player.vtlIconPath} fallback="V" disabled={!player.vtlUrl} onClick={() => player.vtlUrl && bridge?.openVtl?.(player.vtlUrl)} />
          <IconButton label={player.flagTooltip || "Flag player"} icon={player.flagIconPath} fallback="F" active={player.isFlagged} disabled={!player.puuid} onClick={() => dispatch("togglePlayerFlag", { puuid: player.puuid })} />
        </div>
        <button className="weaponStrip" onClick={() => dispatch("openPlayerLoadout", { playerKey: loadoutKey })}>
          {(player.weapons || player.weaponIcons || []).slice(0, 2).map((weapon, index) => <AssetImage key={index} src={weapon.icon || weapon.iconPath} alt={weapon.weaponName || ""} fallback="-" />)}
        </button>
        <div className="statGrid">{stats.map((stat) => <div className={`stat tone-${stat.tone || "neutral"}`} key={stat.label}><span>{stat.label}</span><strong>{dash(stat.value)}</strong></div>)}</div>
      </div>
      <aside className="rankArea">
        <div className="recentDots">
          {(rrChanges.length ? rrChanges.slice(0, 3) : [{ valueText: "0", numericValue: 0 }]).map((change, index) => (
            <span className={`rrDot ${rrTone(change)}`} key={`${index}-${change.valueText || change.text}`}>{dash(change.valueText || change.text || "0")}</span>
          ))}
        </div>
        <div className="peak">
          <AssetImage className="peakIcon" src={player.peakRankIcon || player.peakRankIconPath} alt={player.peakRankText || ""} fallback="" />
          <span>{dash(player.peakActText)}</span>
        </div>
        <div className="currentRank">
          <AssetImage className="rankIcon" src={player.rankIcon || player.rankIconPath} alt={player.rankText || ""} fallback={dash(player.rankText)} />
          <strong>{dash(player.rrText).replace(/\s*RR$/i, "")}</strong>
        </div>
      </aside>
    </article>
  );
}

function InlineIcon({ src, title }: { src?: string; title?: string }) {
  if (!src) return null;
  return <span className="inlineIcon" title={title || ""}><AssetImage src={src} alt="" /></span>;
}

function IconButton({ label, icon, fallback, active, disabled, onClick }: { label: string; icon?: string; fallback: string; active?: boolean; disabled?: boolean; onClick: () => void }) {
  return (
    <button className={`iconButton ${active ? "active" : ""}`} title={label} aria-label={label} disabled={disabled} onClick={onClick}>
      <AssetImage src={icon} alt="" fallback={fallback} />
    </button>
  );
}

function StatusBar({ snapshot, bridgeStatus }: { snapshot: Snapshot; bridgeStatus: string }) {
  return <footer className="status">{snapshot.status?.message || "Ready"} | React renderer: {bridgeStatus} | Theme: {snapshot.theme?.name || "unknown"}</footer>;
}

function ModalLayer({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const modal = snapshot.activeModal;
  if (!modal) return null;
  return (
    <div className="modalBackdrop">
      <section className={`modal modal-${modal}`}>
        <button className="modalClose" title="Close" aria-label="Close" onClick={() => dispatch("dismissModal")}>x</button>
        {snapshot.validationErrors?.map((error) => <div className="error" key={error}>{error}</div>)}
        {modal === "tools" ? <ToolsModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "theme" ? <ThemeModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "agentPicker" ? <AgentModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "mapAgentPicker" ? <MapAgentModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "queueSnipe" ? <QueueModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "loadouts" ? <LoadoutsModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "playerLoadout" ? <PlayerLoadoutModal snapshot={snapshot} /> : null}
        {modal === "flagReason" ? <FlagReasonModal snapshot={snapshot} dispatch={dispatch} /> : null}
        {modal === "restartRisk" ? <RestartModal snapshot={snapshot} dispatch={dispatch} /> : null}
      </section>
    </div>
  );
}

function ModalHeader({ eyebrow, title, detail }: { eyebrow: string; title: string; detail?: string }) {
  return (
    <header className="modalHeader">
      <span>{eyebrow}</span>
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : null}
    </header>
  );
}

function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="emptyState">
      <strong>{title}</strong>
      {detail ? <span>{detail}</span> : null}
    </div>
  );
}

function ToolsModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const presenceMode = snapshot.presence?.mode === "offline" ? "offline" : "online";
  const queueLabel = snapshot.queueSnipe?.selectedFriend?.display_name || "No friend selected";
  return (
    <>
      <ModalHeader eyebrow="Controls" title="Tools" detail="Fast access to queue, presence, themes, and loadout workflows." />
      <div className="toolGrid">
        <button className="toolTile" onClick={() => dispatch("openQueueSnipe")}>
          <span className="tileIcon">QS</span>
          <strong>Queue Snipe</strong>
          <small>{queueLabel}</small>
        </button>
        <button className="toolTile" onClick={() => dispatch("setPresenceMode", { mode: presenceMode === "offline" ? "online" : "offline" })}>
          <span className="tileIcon">{presenceMode === "offline" ? "OFF" : "ON"}</span>
          <strong>Presence</strong>
          <small>{presenceMode === "offline" ? "Appear Offline enabled" : "Online presence"}</small>
        </button>
        <button className="toolTile" onClick={() => dispatch("openThemeModal")}>
          <span className="tileIcon">TH</span>
          <strong>Themes</strong>
          <small>{snapshot.theme?.name || "Current theme"}</small>
        </button>
        <button className="toolTile" onClick={() => dispatch("openLoadouts")}>
          <span className="tileIcon">LD</span>
          <strong>Loadouts</strong>
          <small>{snapshot.ownedLoadoutEditor?.presets?.length || 0} presets</small>
        </button>
      </div>
    </>
  );
}

function ThemeModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const activeTheme = snapshot.theme?.name || "";
  const surfaceMode = snapshot.theme?.surfaceMode || "";
  return (
    <>
      <ModalHeader eyebrow="Appearance" title="Themes" detail="Pick a palette and surface style for the scanner." />
      <div className="themeGrid">
        {(snapshot.theme?.options || []).map((theme) => (
          <button className={`themeSwatch ${theme.name === activeTheme ? "selected" : ""}`} key={theme.name} onClick={() => dispatch("selectTheme", { theme: theme.name })}>
            <span className="swatchPair"><i style={{ background: theme.swatchA }} /><i style={{ background: theme.swatchB }} /></span>
            <strong>{theme.label || theme.name}</strong>
            <small>{theme.name}</small>
          </button>
        ))}
      </div>
      <div className="segmented">
        {(snapshot.theme?.surfaceModes || []).map((mode) => (
          <button className={mode === surfaceMode ? "selected" : ""} key={mode} onClick={() => dispatch("selectTheme", { theme: activeTheme, surfaceMode: mode })}>{mode}</button>
        ))}
      </div>
    </>
  );
}

function AgentModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const options = (snapshot.modalData?.options as AgentOption[]) || snapshot.agentLock?.options || [];
  const selected = snapshot.agentLock?.standardAgent || snapshot.agentLock?.selectedAgent || "";
  return (
    <>
      <ModalHeader eyebrow="Auto Lock" title="Agent Picker" detail="Choose the standard agent used when map-specific locking is disabled." />
      <div className="agentGrid">
        {options.map((agent) => (
          <button className={agent.name === selected ? "selected" : ""} key={agent.name} onClick={() => dispatch("selectAgent", { agent: agent.name })}>
            <AssetImage src={agent.icon} alt="" fallback={agent.name.slice(0, 2)} />
            <strong>{agent.name}</strong>
            <small>{agent.owned === false ? "Unavailable" : "Owned"}</small>
          </button>
        ))}
      </div>
    </>
  );
}

function MapAgentModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const maps = (snapshot.modalData?.maps as MapOption[]) || snapshot.mapAgents?.maps || [];
  const options = (snapshot.modalData?.options as AgentOption[]) || snapshot.mapAgents?.agentOptions || [];
  const selection = (snapshot.modalData?.selection as Record<string, string>) || snapshot.mapAgents?.selection || {};
  return (
    <>
      <ModalHeader eyebrow="Auto Lock" title="Map-Specific Agents" detail="Assign per-map picks or role tokens for map-specific auto lock." />
      <div className="mapRows">
        {maps.map((map) => (
          <label className="mapRow" key={map.uuid}>
            <span>{map.name}</span>
            <select value={selection[map.uuid] || ""} onChange={(event) => dispatch("selectMapAgent", { mapUuid: map.uuid, agent: event.target.value })}>
              <option value="">None</option>
              {options.map((agent) => <option key={agent.name} value={agent.name}>{agent.name}</option>)}
            </select>
          </label>
        ))}
      </div>
    </>
  );
}

function QueueModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const queue = snapshot.queueSnipe || {};
  const friends = queue.friends || [];
  return (
    <>
      <ModalHeader eyebrow="Party Tools" title="Queue Snipe" detail="Select a friend and toggle queue snipe tracking." />
      <div className="queueSummary">
        <div><span>Selected</span><strong>{queue.selectedFriend?.display_name || "None"}</strong></div>
        <Toggle label="Enabled" checked={Boolean(queue.enabled)} disabled={!queue.selectedFriend} onChange={(enabled) => dispatch("setQueueSnipeEnabled", { enabled })} />
      </div>
      {queue.loading ? <EmptyState title="Loading friends..." detail="Fetching your Riot friends list." /> : null}
      {queue.error ? <div className="error">{queue.error}</div> : null}
      {!queue.loading && friends.length === 0 ? <EmptyState title="No friends loaded" detail="Open Queue Snipe again after Riot social data is available." /> : null}
      <div className="friendGrid">
        {friends.map((friend) => (
          <button className={friend.puuid === queue.selectedFriend?.puuid ? "selected" : ""} key={friend.puuid} onClick={() => dispatch("setQueueSnipeFriend", { friend })}>
            <strong>{friend.display_name || friend.game_name || friend.puuid}</strong>
            <small>{friend.game_name && friend.game_tag ? `${friend.game_name}#${friend.game_tag}` : friend.puuid}</small>
          </button>
        ))}
      </div>
    </>
  );
}

function LoadoutsModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const editor = snapshot.ownedLoadoutEditor || {};
  const [presetName, setPresetName] = useState("");
  return (
    <>
      <ModalHeader eyebrow="Collection" title="Loadouts" detail="Review your current loadout, save presets, and apply existing presets." />
      {editor.loading ? <EmptyState title="Loading loadouts..." detail="Fetching owned skins and current equipment." /> : null}
      <div className="loadoutLayout">
        <aside className="presetPanel">
          <div className="panelTitle"><span>Presets</span><strong>{editor.selectedPreset || "Current Loadout"}</strong></div>
          <div className="presetList">
            {(editor.presets || []).map((preset) => (
              <button className={preset === editor.selectedPreset ? "selected" : ""} key={preset} onClick={() => dispatch("applyPreset", { name: preset })}>{preset}</button>
            ))}
          </div>
          <div className="savePreset">
            <input value={presetName} onChange={(event) => setPresetName(event.target.value)} placeholder="Preset name" />
            <button className="accentButton" onClick={() => dispatch("savePreset", { name: presetName })}>Save</button>
          </div>
        </aside>
        <div className="weaponGrid">
          {(editor.weapons || []).map((weapon) => (
            <div className="weaponCard" key={weapon.weapon}>
              <AssetImage src={weapon.skinIcon} alt="" fallback="-" />
              <strong>{weapon.weapon}</strong>
              <span>{weapon.skinName || weapon.skinId || "No skin"}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function PlayerLoadoutModal({ snapshot }: { snapshot: Snapshot }) {
  const data = snapshot.playerLoadouts || {};
  return (
    <>
      <ModalHeader eyebrow="Player Cosmetics" title={data.playerName || "Player Loadout"} detail="Equipped skins and buddies detected for this player." />
      <div className="weaponGrid">
        {(data.weapons || []).map((weapon) => (
          <div className="weaponCard" key={weapon.weapon}>
            <AssetImage src={weapon.skinIcon} alt="" fallback="-" />
            <strong>{weapon.weapon}</strong>
            <span>{weapon.skinName || weapon.skinId || "No skin"}</span>
          </div>
        ))}
      </div>
    </>
  );
}

function FlagReasonModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const [reason, setReason] = useState("");
  const puuid = String(snapshot.modalData?.puuid || "");
  return (
    <>
      <ModalHeader eyebrow="Flagged Player" title="Reason" detail="Add a short note so this flag is useful later." />
      <div className="formStack">
        <input autoFocus value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Enter reason" />
        <div className="modalActions"><button className="accentButton" onClick={() => dispatch("submitFlagReason", { puuid, reason })}>Submit</button></div>
      </div>
    </>
  );
}

function RestartModal({ snapshot, dispatch }: { snapshot: Snapshot; dispatch: (command: string, payload?: Record<string, unknown>) => void }) {
  const prompt = snapshot.prompts?.restart || {};
  return (
    <>
      <ModalHeader eyebrow="Startup" title={prompt.title || "Restart Riot Client"} detail={prompt.message} />
      <div className="warningPanel">
        <span>Currently running</span>
        <strong>{prompt.runningProcesses}</strong>
      </div>
      <div className="modalActions"><button className="danger" onClick={() => dispatch("confirmRestart", { confirmed: true })}>Yes, Launch Valorant</button><button onClick={() => dispatch("confirmRestart", { confirmed: false })}>No, Keep Disabled</button></div>
    </>
  );
}

function LoadingOverlay({ status }: { status: NonNullable<Snapshot["status"]> }) {
  const loaded = status.progress?.loaded || 0;
  const total = status.progress?.total || 0;
  const width = total > 0 ? `${Math.min(100, (loaded / total) * 100)}%` : "25%";
  return <div className="loading"><div><h2>ValScanner</h2><p>{status.message || "Loading..."}</p><div className="progress"><span style={{ width }} /></div></div></div>;
}

function AssetImage({ src, alt, className, fallback }: { src?: string; alt: string; className?: string; fallback?: string }) {
  const [broken, setBroken] = useState(false);
  if (!src || broken) return <span className={`assetFallback ${className || ""}`}>{fallback || ""}</span>;
  return <img className={className} src={src} alt={alt} onError={() => setBroken(true)} draggable={false} />;
}
