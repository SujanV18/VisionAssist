import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Aperture,
  ArrowUpRight,
  ArrowRight,
  LayoutDashboard,
  Package,
  LogOut,
  ShieldCheck,
  Search,
  Plus,
  X,
  FileText,
  Link,
  Users,
  Check,
  MapPin,
  Clock,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import {
  api,
  money,
  date,
  statusName,
  type User,
  type Product,
  type Enquiry,
  type Line,
  type Quote,
} from "./api";
import "./styles.css";

function Brand() {
  return (
    <a className="brand" href="/">
      <span className="brand-mark">
        <Aperture size={25} />
      </span>
      <span>
        VisionAssist<span className="brand-sub">SALES OPERATIONS</span>
      </span>
    </a>
  );
}
function ErrorMessage({ message }: { message: string }) {
  return message ? (
    <div className="error" role="alert">
      {message}
    </div>
  ) : null;
}
function Badge({ status }: { status: string }) {
  return (
    <span className={"badge " + status}>
      <span />
      {statusName(status)}
    </span>
  );
}
function App() {
  const path = window.location.pathname;
  if (path === "/enquire") return <Customer />;
  if (path === "/track") return <Tracking />;
  return <Staff />;
}
function Staff() {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  if (loading)
    return (
      <div className="loading">
        <Aperture /> Opening your workspace…
      </div>
    );
  if (!user) return <Login onLogin={setUser} />;
  async function logout() {
    try {
      await api("/auth/logout", "POST");
      setUser(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return <Workspace user={user} logout={logout} sessionError={error} />;
}
function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState("manager@visionassist.demo"),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api<User>("/auth/login", "POST", { email, password }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-layout">
      <section className="login-story">
        <Brand />
        <div>
          <span className="eyebrow light">FROM ENQUIRY TO CONFIDENCE</span>
          <h1>
            A clearer view.
            <br />A better sales journey.
          </h1>
          <p>
            One place to understand customer needs, coordinate your team, and
            prepare thoughtful CCTV proposals.
          </p>
          <div className="journey">
            <span>01&nbsp; Capture</span>
            <ArrowRight />
            <span>02&nbsp; Connect</span>
            <ArrowRight />
            <span>03&nbsp; Quote</span>
          </div>
        </div>
        <small>VisionAssist · 5th-semester entrepreneurship prototype</small>
      </section>
      <main className="login-main">
        <div className="login-card">
          <span className="eyebrow">YOUR WORKSPACE</span>
          <h2>Welcome back.</h2>
          <p className="muted">Sign in to move the next enquiry forward.</p>
          <form onSubmit={submit}>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </label>
            <ErrorMessage message={error} />
            <button className="primary wide" disabled={busy}>
              {busy ? "Signing in…" : "Open workspace"}
              <ArrowRight size={18} />
            </button>
          </form>
          <details className="demo-help">
            <summary>Local demo accounts</summary>
            <p>
              Choose manager, Arjun, or Priya. All demo passwords:{" "}
              <code>VisionDemo!2026</code>
            </p>
            <div className="demo-buttons">
              {["manager", "arjun", "priya"].map((n) => (
                <button
                  key={n}
                  onClick={() => {
                    setEmail(n + "@visionassist.demo");
                    setPassword("VisionDemo!2026");
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
            <small>Synthetic enquiries and illustrative prices only.</small>
          </details>
          <a className="text-link" href="/enquire">
            Looking for CCTV? Make an enquiry <ArrowUpRight size={16} />
          </a>
        </div>
        <p className="login-footer">
          <ShieldCheck size={15} /> Local college prototype · no paid services
        </p>
      </main>
    </div>
  );
}
function Workspace({
  user,
  logout,
  sessionError,
}: {
  user: User;
  logout: () => void;
  sessionError: string;
}) {
  const [tab, setTab] = useState("enquiries"),
    [enquiries, setEnquiries] = useState<Enquiry[]>([]),
    [products, setProducts] = useState<Product[]>([]),
    [team, setTeam] = useState<User[]>([]),
    [selected, setSelected] = useState<string | null>(null),
    [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [copied, setCopied] = useState(false);
  const manager = user.role === "manager";
  async function refresh() {
    setError("");
    try {
      const [es, ps, ts] = await Promise.all([
        api<Enquiry[]>("/enquiries"),
        api<Product[]>("/catalogue"),
        manager ? api<User[]>("/team") : Promise.resolve([]),
      ]);
      setEnquiries(es);
      setProducts(ps);
      setTeam(ts);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
  const visible = enquiries.filter(
    (e) =>
      (filter === "all" ||
        (filter === "unassigned" ? !e.assignee_id : e.status === filter)) &&
      `${e.name} ${e.location} ${e.property_type}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const referral =
    window.location.origin + "/enquire?ref=" + user.referral_code;
  async function copyReferral() {
    try {
      await navigator.clipboard.writeText(referral);
      setCopied(true);
    } catch {
      setError("Copy the referral link shown below manually.");
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-label">WORKSPACE</div>
        <nav>
          <button
            className={tab === "enquiries" ? "active" : ""}
            onClick={() => setTab("enquiries")}
          >
            <LayoutDashboard size={19} />
            Enquiries<span className="nav-count">{enquiries.length}</span>
          </button>
          <button
            className={tab === "catalogue" ? "active" : ""}
            onClick={() => setTab("catalogue")}
          >
            <Package size={19} />
            Product catalogue
          </button>
        </nav>
        <div className="sidebar-note">
          <ShieldCheck size={22} />
          <strong>Built on verified details</strong>
          <p>
            Traceable datasheets.
            <br />
            Clear ownership.
            <br />
            Reviewed proposals.
          </p>
        </div>
        <div className="profile">
          <span className="avatar">
            {user.name
              .split(" ")
              .map((n) => n[0])
              .join("")}
          </span>
          <div>
            <strong>{user.name}</strong>
            <small>{manager ? "Sales manager" : "Salesperson"}</small>
          </div>
          <button
            className="icon-button"
            aria-label="Sign out"
            onClick={logout}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <span className="muted">Workspace</span>
            <ChevronRight size={14} />
            <span>{tab === "enquiries" ? "Enquiries" : "Catalogue"}</span>
          </div>
          <span className="local-indicator">
            <i /> LOCAL PROTOTYPE
          </span>
        </header>
        <main className="main-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {manager ? "TEAM PIPELINE" : "YOUR PIPELINE"}
              </span>
              <h1>
                {tab === "enquiries"
                  ? "Every enquiry, a next step."
                  : "Know what you’re proposing."}
              </h1>
              <p className="muted">
                {tab === "enquiries"
                  ? manager
                    ? "A shared view of customer needs and the people taking them forward."
                    : "Your customers, their requirements, and the next proposal to prepare."
                  : "A small, source-checked catalogue. Expand it one verified model at a time."}
              </p>
            </div>
            <a
              className="primary"
              href="/enquire"
              target="_blank"
              rel="noreferrer"
            >
              <Plus size={17} />
              New enquiry
            </a>
          </div>
          <ErrorMessage message={error || sessionError} />
          {tab === "enquiries" ? (
            <>
              <div className="stats">
                <Stat
                  label={manager ? "Total enquiries" : "Assigned to you"}
                  count={enquiries.length}
                  icon={<Users />}
                />
                <Stat
                  label="Awaiting assignment"
                  count={enquiries.filter((e) => !e.assignee_id).length}
                  icon={<Clock />}
                />
                <Stat
                  label="Ready to review"
                  count={
                    enquiries.filter((e) => e.status === "assigned").length
                  }
                  icon={<ShieldCheck />}
                />
                <Stat
                  label="Drafts in progress"
                  count={
                    enquiries.filter((e) => e.status === "drafting").length
                  }
                  icon={<FileText />}
                />
              </div>
              <section className="panel pipeline">
                <div className="panel-heading">
                  <div>
                    <h2>
                      {manager ? "Enquiry inbox" : "My enquiries"}{" "}
                      <span className="count">{enquiries.length}</span>
                    </h2>
                    <p className="muted">
                      {manager
                        ? "Assign a next step. Keep the original referral intact."
                        : "Open an enquiry to review requirements and build a draft."}
                    </p>
                  </div>
                  <button
                    className="secondary"
                    onClick={() => void refresh()}
                    aria-label="Refresh enquiries"
                  >
                    <RefreshCw size={16} />
                    Refresh
                  </button>
                </div>
                <div className="toolbar">
                  <div className="tabs">
                    {[
                      ["all", "All enquiries"],
                      ...(manager ? [["unassigned", "Unassigned"]] : []),
                      ["assigned", "Assigned"],
                      ["drafting", "Drafting"],
                    ].map(([key, title]) => (
                      <button
                        key={key}
                        className={filter === key ? "chosen" : ""}
                        onClick={() => setFilter(key)}
                      >
                        {title}
                      </button>
                    ))}
                  </div>
                  <label className="search">
                    <Search size={17} />
                    <input
                      aria-label="Search enquiries"
                      placeholder="Search enquiries…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </label>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Customer / property</th>
                        <th>Location</th>
                        <th>Source</th>
                        <th>Assigned to</th>
                        <th>Status</th>
                        <th>
                          <span className="sr-only">Open</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((e) => (
                        <tr key={e.id}>
                          <td>
                            <button
                              className="row-link"
                              onClick={() => setSelected(e.id)}
                            >
                              {e.name}
                            </button>
                            <small>
                              {e.property_type} · {date(e.created_at)}
                            </small>
                          </td>
                          <td>{e.location}</td>
                          <td>
                            <span className="source">
                              {e.original_referrer_name ? (
                                <>
                                  <Link size={13} />
                                  {e.original_referrer_name}
                                </>
                              ) : (
                                <>Website enquiry</>
                              )}
                            </span>
                          </td>
                          <td>
                            {e.assignee_name || (
                              <span className="muted">Unassigned</span>
                            )}
                          </td>
                          <td>
                            <Badge status={e.status} />
                          </td>
                          <td>
                            <button
                              className="icon-button"
                              aria-label={"Open " + e.name}
                              onClick={() => setSelected(e.id)}
                            >
                              <ArrowUpRight size={19} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!visible.length && (
                  <div className="empty">
                    {loading
                      ? "Loading enquiries…"
                      : "No enquiries match this view."}
                  </div>
                )}
                <div className="panel-bottom">
                  <ShieldCheck size={14} />{" "}
                  {manager
                    ? "Assignments are recorded in each enquiry’s history."
                    : "Only enquiries currently assigned to you appear here."}
                  <span>
                    Showing {visible.length} of {enquiries.length} · latest 200
                    maximum
                  </span>
                </div>
              </section>
              <div className="bottom-grid">
                <section className="next-card">
                  <span className="eyebrow">A SIMPLE WORKFLOW</span>
                  <h3>Good proposals start with good context.</h3>
                  <p>
                    Review the requirement, choose a verified model and lens,
                    then save a quotation draft for review.
                  </p>
                  <div className="mini-steps">
                    <span>Enquiry</span>
                    <ArrowRight size={15} />
                    <span>Assignment</span>
                    <ArrowRight size={15} />
                    <span>Draft</span>
                  </div>
                </section>
                <section className="panel small-panel">
                  <div className="small-icon">
                    <Link size={20} />
                  </div>
                  <h3>
                    {manager
                      ? "Two ways in. One clear owner."
                      : "Your personal enquiry link"}
                  </h3>
                  <p className="muted">
                    {manager
                      ? "General enquiries arrive unassigned. Referral enquiries go directly to the referring salesperson."
                      : "Customers using this link are automatically assigned to you."}
                  </p>
                  {!manager ? (
                    <>
                      <input
                        className="copy-input"
                        aria-label="Your referral link"
                        readOnly
                        value={referral}
                      />
                      <button className="text-link" onClick={copyReferral}>
                        {copied ? <Check size={15} /> : <Link size={15} />}{" "}
                        {copied ? "Copied" : "Copy referral link"}
                      </button>
                    </>
                  ) : (
                    <a
                      className="text-link"
                      href="/enquire"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Preview customer form
                      <ArrowUpRight size={16} />
                    </a>
                  )}
                </section>
              </div>
            </>
          ) : (
            <>
              <div className="notice">
                <ShieldCheck size={18} />
                <span>
                  <strong>3 reviewed models · 66 source PDFs inspected.</strong>{" "}
                  Prices below are invented demo amounts for workflow testing.
                  No live price or stock feed.
                </span>
              </div>
              <div className="catalogue-grid">
                {products.map((p) => (
                  <ProductCard key={p.id} p={p} />
                ))}
              </div>
            </>
          )}
          <footer className="workspace-footer">
            VisionAssist · College entrepreneurship project
            <span>Milestone 01 / Enquiry to quotation draft</span>
          </footer>
        </main>
      </div>
      {selected && (
        <EnquiryDetail
          key={selected}
          id={selected}
          user={user}
          products={products}
          team={team}
          close={() => setSelected(null)}
          changed={refresh}
        />
      )}
    </div>
  );
}
function Stat({
  label,
  count,
  icon,
}: {
  label: string;
  count: number;
  icon: React.ReactNode;
}) {
  return (
    <div className="stat">
      <div>
        <span>{label}</span>
        <strong>{String(count).padStart(2, "0")}</strong>
      </div>
      <span className="stat-icon">{icon}</span>
    </div>
  );
}
function ProductCard({ p }: { p: Product }) {
  return (
    <article className="panel product-card">
      <div className="product-top">
        <Package size={32} />
        <span className="verified">
          <ShieldCheck size={13} />
          Source checked
        </span>
      </div>
      <span className="eyebrow">PRAMA DATASHEET</span>
      <h3>{p.model}</h3>
      <p className="muted">{p.title}</p>
      <dl>
        <div>
          <dt>Resolution</dt>
          <dd>{p.specs.resolution}</dd>
        </div>
        <div>
          <dt>Lens options</dt>
          <dd>{p.specs.lens_options.join(" / ")}</dd>
        </div>
        <div>
          <dt>IR range</dt>
          <dd>{p.specs.ir_range}</dd>
        </div>
        <div>
          <dt>Protection / WDR</dt>
          <dd>
            {p.specs.protection} / {p.specs.wdr}
          </dd>
        </div>
      </dl>
      <div className="product-price">
        <strong>{money(p.price_paise)}</strong>
        <span>DEMO PRICE ONLY</span>
      </div>
      <a
        className="text-link"
        href={"/api/catalogue/" + p.id + "/source"}
        target="_blank"
        rel="noreferrer"
      >
        View source datasheet
        <ArrowUpRight size={15} />
      </a>
      <small className="evidence">
        Specifications: pages 2–3 · Title: page 1
      </small>
    </article>
  );
}
function EnquiryDetail({
  id,
  user,
  products,
  team,
  close,
  changed,
}: {
  id: string;
  user: User;
  products: Product[];
  team: User[];
  close: () => void;
  changed: () => Promise<void>;
}) {
  const [detail, setDetail] = useState<Enquiry | null>(null),
    [assignee, setAssignee] = useState(""),
    [reason, setReason] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [lines, setLines] = useState<Line[]>([]),
    [notes, setNotes] = useState(""),
    [saved, setSaved] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  async function load() {
    const d = await api<Enquiry>("/enquiries/" + id);
    setDetail(d);
    setAssignee(d.assignee_id || "");
  }
  useEffect(() => {
    dialog.current?.showModal();
    void load().catch((e) => setError(e.message));
  }, []);
  async function assign(e: React.FormEvent) {
    e.preventDefault();
    if (!detail) return;
    setBusy(true);
    setError("");
    try {
      await api("/enquiries/" + id + "/assignment", "POST", {
        assignee_id: assignee || null,
        revision: detail.revision,
        reason,
      });
      await load();
      await changed();
      setReason("");
      setSaved("Assignment updated. The original referral has been preserved.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveQuote(e: React.FormEvent) {
    e.preventDefault();
    if (!detail) return;
    setBusy(true);
    setError("");
    try {
      const q = await api<Quote>("/enquiries/" + id + "/quotations", "POST", {
        items: lines,
        notes,
        revision: detail.revision,
      });
      await load();
      await changed();
      setSaved(
        `Draft v${q.version} saved. It has not been sent to the customer.`,
      );
      setLines([]);
      setNotes("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function add(p: Product) {
    setLines([...lines, { product_id: p.id, quantity: 1, lens: "2.8 mm" }]);
    setSaved("");
  }
  const total = lines.reduce(
    (n, l) =>
      n +
      (products.find((p) => p.id === l.product_id)?.price_paise || 0) *
        l.quantity,
    0,
  );
  return (
    <dialog className="detail-dialog" ref={dialog} onCancel={close}>
      <div className="drawer-header">
        <span className="eyebrow">ENQUIRY DETAILS</span>
        <button
          aria-label="Close enquiry"
          className="icon-button"
          onClick={close}
        >
          <X />
        </button>
      </div>
      <div className="drawer-body">
        <ErrorMessage message={error} />
        {saved && (
          <div className="success" role="status">
            <Check size={16} />
            {saved}
          </div>
        )}
        {detail ? (
          <>
            <div className="detail-title">
              <h2>{detail.name}</h2>
              <Badge status={detail.status} />
            </div>
            <p className="muted">
              <MapPin size={14} /> {detail.property_type} · {detail.location}
            </p>
            <div className="contact-box">
              <span>
                Contact<strong>{detail.contact}</strong>
              </span>
              <span>
                Current owner
                <strong>{detail.assignee_name || "Unassigned"}</strong>
              </span>
              <span>
                Original referral
                <strong>
                  {detail.original_referrer_name || "General enquiry"}
                </strong>
              </span>
            </div>
            <section className="detail-section">
              <h3>What the customer needs</h3>
              <p className="requirements">{detail.requirements}</p>
            </section>
            {user.role === "manager" ? (
              <section className="detail-section">
                <h3>Assign the next step</h3>
                <form onSubmit={assign}>
                  <label>
                    Salesperson
                    <select
                      value={assignee}
                      onChange={(e) => setAssignee(e.target.value)}
                    >
                      <option value="">Unassigned</option>
                      {team.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Reason for assignment
                    <input
                      required
                      minLength={3}
                      maxLength={500}
                      placeholder="e.g. Area coverage and availability"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </label>
                  <button
                    className="primary"
                    disabled={busy || assignee === (detail.assignee_id || "")}
                  >
                    Save assignment
                    <ArrowRight size={16} />
                  </button>
                </form>
              </section>
            ) : (
              <section className="detail-section">
                <div className="section-title">
                  <h3>Build a quotation draft</h3>
                  <span className="demo-label">DEMO PRICES</span>
                </div>
                <p className="muted">
                  Select verified products. Confirm the lens variant and
                  quantity.
                </p>
                <div className="product-picks">
                  {products.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => add(p)}
                      disabled={lines.length >= 20}
                    >
                      <Plus size={15} />
                      <span>
                        {p.model}
                        <small>{money(p.price_paise)} · demo / unit</small>
                      </span>
                    </button>
                  ))}
                </div>
                <form onSubmit={saveQuote}>
                  {lines.map((line, i) => {
                    const p = products.find((p) => p.id === line.product_id)!;
                    return (
                      <div className="quote-line" key={i}>
                        <strong>{p.model}</strong>
                        <label>
                          Lens
                          <select
                            value={line.lens}
                            onChange={(e) =>
                              setLines(
                                lines.map((l, j) =>
                                  j === i ? { ...l, lens: e.target.value } : l,
                                ),
                              )
                            }
                          >
                            {p.specs.lens_options.map((l) => (
                              <option key={l}>{l}</option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Qty
                          <input
                            type="number"
                            min={1}
                            max={100}
                            required
                            value={line.quantity}
                            onChange={(e) =>
                              setLines(
                                lines.map((l, j) =>
                                  j === i
                                    ? { ...l, quantity: Number(e.target.value) }
                                    : l,
                                ),
                              )
                            }
                          />
                        </label>
                        <button
                          type="button"
                          aria-label={"Remove line " + (i + 1)}
                          className="icon-button"
                          onClick={() =>
                            setLines(lines.filter((_, j) => i !== j))
                          }
                        >
                          <X size={16} />
                        </button>
                      </div>
                    );
                  })}
                  <label>
                    Draft notes
                    <textarea
                      maxLength={2000}
                      placeholder="Scope assumptions, installation items still to confirm…"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                  </label>
                  <div className="quote-total">
                    <span>Demo equipment subtotal</span>
                    <strong>{money(total)}</strong>
                  </div>
                  <p className="fine-print">
                    Equipment only. Tax, installation, cabling, storage,
                    delivery and availability are not assessed. This is not a
                    commercial offer.
                  </p>
                  <button
                    className="primary wide"
                    disabled={busy || !lines.length}
                  >
                    <FileText size={17} />
                    {busy ? "Saving…" : "Save private draft"}
                  </button>
                </form>
              </section>
            )}
            <section className="detail-section">
              <h3>
                Quotation versions{" "}
                <span className="count">{detail.quotations?.length || 0}</span>
              </h3>
              {detail.quotations?.length ? (
                detail.quotations.map((q) => (
                  <details className="quote-version" key={q.id}>
                    <summary>
                      <span>
                        Draft v{q.version} <small>{date(q.created_at)}</small>
                      </span>
                      <strong>{money(q.total_paise)}</strong>
                    </summary>
                    <div className="demo-warning">
                      DEMO PRICES · PRIVATE DRAFT · NOT SENT
                    </div>
                    {q.items.map((l, i) => (
                      <div className="saved-line" key={i}>
                        <span>
                          {l.model}
                          <small>
                            {l.lens} · {l.quantity} ×{" "}
                            {money(l.unit_price_paise)}
                          </small>
                        </span>
                        <strong>{money(l.line_total_paise)}</strong>
                      </div>
                    ))}
                    {q.notes && <p>{q.notes}</p>}
                    <p className="fine-print">
                      Equipment subtotal only. Taxes and services excluded;
                      confirm full scope before any real proposal.
                    </p>
                    {user.role === "salesperson" && (
                      <button
                        className="secondary"
                        onClick={() => {
                          setLines(
                            q.items.map((l) => ({
                              product_id: l.product_id,
                              quantity: l.quantity,
                              lens: l.lens,
                            })),
                          );
                          setNotes(q.notes);
                          setSaved(
                            "Copied selections into the builder. A new version will use current catalogue prices.",
                          );
                        }}
                      >
                        Use as next draft
                      </button>
                    )}
                  </details>
                ))
              ) : (
                <p className="empty-inline">
                  No quotation yet.{" "}
                  {user.role === "manager"
                    ? "The assigned salesperson can prepare the first draft."
                    : "Select a product above to begin."}
                </p>
              )}
            </section>
            <section className="detail-section">
              <h3>Activity & ownership history</h3>
              <ol className="timeline">
                {detail.history?.map((h) => (
                  <li key={h.id}>
                    <strong>{h.action.replaceAll("_", " ")}</strong>
                    <small>
                      {h.actor} · {date(h.created_at)}
                    </small>
                    {h.details.reason && (
                      <p>
                        {String(h.details.from_name)} →{" "}
                        {String(h.details.to_name)}
                        <br />
                        {h.details.reason}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          </>
        ) : (
          !error && <p>Loading enquiry…</p>
        )}
      </div>
    </dialog>
  );
}
function PublicHeader() {
  return (
    <header className="public-header">
      <Brand />
      <a href="/" className="text-link">
        Staff sign in <ArrowUpRight size={16} />
      </a>
    </header>
  );
}
function Customer() {
  const ref = new URLSearchParams(window.location.search).get("ref");
  const [referral, setReferral] = useState(""),
    [error, setError] = useState(""),
    [refError, setRefError] = useState(""),
    [busy, setBusy] = useState(false),
    [receipt, setReceipt] = useState<{ tracking_token: string } | null>(null),
    [copied, setCopied] = useState(false);
  useEffect(() => {
    if (ref)
      api<{ name: string }>("/public/referral/" + encodeURIComponent(ref))
        .then((r) => setReferral(r.name))
        .catch((e) => setRefError(e.message));
  }, [ref]);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      setReceipt(
        await api("/public/enquiries", "POST", {
          ...data,
          consent: data.consent === "on",
          referral_code: ref,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const trackingLink = receipt
    ? window.location.origin + "/track#" + receipt.tracking_token
    : "";
  return (
    <div className="public-page">
      <PublicHeader />
      <main className="customer-grid">
        <section className="customer-intro">
          <span className="eyebrow">LET’S UNDERSTAND YOUR SPACE</span>
          <h1>
            Better security
            <br />
            starts with a<br />
            <em>conversation.</em>
          </h1>
          <p>
            Tell us what you want to protect. A salesperson can review your
            needs and help you plan a suitable CCTV setup.
          </p>
          <div className="public-steps">
            {[
              [
                "01",
                "Tell us about your property",
                "A few details help us ask the right questions.",
              ],
              [
                "02",
                "Connect with a salesperson",
                "Your enquiry reaches the right person.",
              ],
              [
                "03",
                "Plan your proposal",
                "Requirements first. A reviewed quote next.",
              ],
            ].map(([n, t, d]) => (
              <div key={n}>
                <span>{n}</span>
                <div>
                  <strong>{t}</strong>
                  <p>{d}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="prototype-note">
            <ShieldCheck size={18} />
            <span>
              College prototype. Use demo contact details while trying the
              workflow.
            </span>
          </div>
        </section>
        <section className="panel enquiry-form">
          {receipt ? (
            <>
              <span className="success-icon">
                <Check />
              </span>
              <h2>Your enquiry is in.</h2>
              <p>
                Keep this private link to check progress. It expires in 30 days.
                Anyone with the link can see this enquiry’s limited status.
              </p>
              <label>
                Your private tracking link
                <input readOnly value={trackingLink} />
              </label>
              <button
                className="secondary wide"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(trackingLink);
                    setCopied(true);
                  } catch {
                    setError("Please copy the tracking link manually.");
                  }
                }}
              >
                {copied ? "Copied" : "Copy tracking link"}
              </button>
              <a className="primary wide" href={trackingLink}>
                Track my enquiry <ArrowRight size={16} />
              </a>
              <ErrorMessage message={error} />
            </>
          ) : (
            <>
              <span className="eyebrow">NEW ENQUIRY</span>
              <h2>A little context goes a long way.</h2>
              <p className="muted">
                No account needed. Your details are visible to the responsible
                sales team.
              </p>
              {ref && (
                <div className="notice">
                  <Link size={17} />
                  {referral
                    ? "You’re enquiring with " + referral
                    : refError || "Checking referral…"}
                </div>
              )}
              {refError && (
                <a className="text-link" href="/enquire">
                  Use the general enquiry form instead
                </a>
              )}
              <form onSubmit={submit}>
                <label>
                  Your name
                  <input
                    name="name"
                    minLength={2}
                    maxLength={100}
                    required
                    placeholder="e.g. Alex Kumar"
                    autoComplete="name"
                  />
                </label>
                <label>
                  Email or phone
                  <input
                    name="contact"
                    minLength={7}
                    maxLength={254}
                    required
                    placeholder="How can the team reach you?"
                  />
                </label>
                <div className="form-row">
                  <label>
                    Property type
                    <select name="property_type">
                      {["Home", "Shop", "Office", "Warehouse", "Other"].map(
                        (t) => (
                          <option key={t}>{t}</option>
                        ),
                      )}
                    </select>
                  </label>
                  <label>
                    Area / city
                    <input
                      name="location"
                      minLength={2}
                      maxLength={200}
                      required
                      placeholder="e.g. Jayanagar, Bengaluru"
                    />
                  </label>
                </div>
                <label>
                  What do you need?
                  <textarea
                    name="requirements"
                    minLength={10}
                    maxLength={4000}
                    required
                    placeholder="Areas to cover, approximate camera count, lighting, or concerns…"
                  />
                </label>
                <label className="checkbox">
                  <input type="checkbox" name="consent" required />
                  <span>
                    I agree to share these details with the sales team so they
                    can respond to this enquiry.
                  </span>
                </label>
                <ErrorMessage message={error} />
                <button
                  className="primary wide"
                  disabled={busy || !!refError || (!!ref && !referral)}
                >
                  {busy ? "Submitting…" : "Send enquiry"}
                  <ArrowRight size={17} />
                </button>
                <p className="fine-print">
                  You’ll receive a private tracking link after submitting. No
                  automated email or SMS is sent in this prototype.
                </p>
              </form>
            </>
          )}
        </section>
      </main>
      <footer className="public-footer">
        VisionAssist · College entrepreneurship prototype · PRAMA datasheets
        used as reference material
      </footer>
    </div>
  );
}
function Tracking() {
  const [data, setData] = useState<{
      id: string;
      status: string;
      property_type: string;
      salesperson: string | null;
      message: string;
    } | null>(null),
    [error, setError] = useState("");
  const token = useRef(window.location.hash.slice(1));
  async function refresh() {
    setError("");
    try {
      setData(
        await api("/public/tracking", "GET", undefined, {
          "X-Tracking-Token": token.current,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
  return (
    <div className="public-page">
      <PublicHeader />
      <main className="tracking panel">
        <span className="eyebrow">PRIVATE ENQUIRY TRACKING</span>
        <h1>Your next step, in view.</h1>
        <ErrorMessage message={error} />
        {data ? (
          <>
            <Badge status={data.status} />
            <p>{data.message}</p>
            <dl>
              <div>
                <dt>Property</dt>
                <dd>{data.property_type}</dd>
              </div>
              <div>
                <dt>Salesperson</dt>
                <dd>{data.salesperson || "Awaiting assignment"}</dd>
              </div>
              <div>
                <dt>Reference</dt>
                <dd>{data.id.slice(0, 8).toUpperCase()}</dd>
              </div>
            </dl>
            <button className="secondary" onClick={() => void refresh()}>
              <RefreshCw size={16} />
              Refresh status
            </button>
            <p className="fine-print">
              Keep this link private. Tracking access expires 30 days after
              submission.
            </p>
          </>
        ) : (
          !error && <p>Checking your enquiry…</p>
        )}
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
