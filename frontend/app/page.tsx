"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  StoryValidationRequest,
  StoryValidationResponse,
  validateStoryStream,
} from "@/lib/api";

const emptyForm: StoryValidationRequest = {
  title: "",
  story: "",
  acceptanceCriteria: [],
  priority: "",
  estimate: "",
  dependencies: [],
};

const exampleStories: StoryValidationRequest[] = [
  {
    title: "Export readiness report",
    story:
      "As a product owner, I want to export story validation results so that I can share readiness feedback with my delivery team.",
    acceptanceCriteria: [
      "Given a validated story, when I request an export, then the API should return the validation results.",
      "The export must include the readiness score and failed checks.",
    ],
    priority: "High",
    estimate: "3",
    dependencies: ["none"],
  },
  {
    title: "Save draft story",
    story:
      "As a business analyst, I want to save a draft story so that I can finish refinement later.",
    acceptanceCriteria: [
      "Given an incomplete story, when I save it, then the draft should be available when I return.",
      "The page must show the saved timestamp.",
    ],
    priority: "Medium",
    estimate: "2",
    dependencies: ["Authentication"],
  },
];

function listToText(items: string[]) {
  return items.join("\n");
}

function textToList(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function Home() {
  const [form, setForm] = useState<StoryValidationRequest>(emptyForm);
  const [criteriaText, setCriteriaText] = useState("");
  const [dependenciesText, setDependenciesText] = useState("");
  const [result, setResult] = useState<StoryValidationResponse | null>(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const failedChecks = useMemo(
    () => result?.checks.filter((check) => !check.passed) ?? [],
    [result],
  );

  const passedChecks = useMemo(
    () => result?.checks.filter((check) => check.passed).length ?? 0,
    [result],
  );

  const classificationScores = useMemo(
    () =>
      Object.entries(result?.classification?.scores ?? {}).sort(
        ([, firstScore], [, secondScore]) => secondScore - firstScore,
      ),
    [result],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const payload = {
        ...form,
        acceptanceCriteria: textToList(criteriaText),
        dependencies: textToList(dependenciesText),
      };

      setResult({
        readyForWork: false,
        score: 0,
        status: "Validating",
        checks: [],
        suggestions: [],
        classification: null,
      });

      await validateStoryStream(payload, (event) => {
        if (event.type === "rules_complete") {
          setResult((currentResult) => ({
            readyForWork: false,
            score: 0,
            status: "Running AI validation",
            checks: event.checks,
            suggestions: event.suggestions,
            classification: currentResult?.classification ?? null,
          }));
          return;
        }

        if (event.type === "ai_complete") {
          setResult((currentResult) => ({
            readyForWork: false,
            score: 0,
            status: "Calculating score",
            checks: [...(currentResult?.checks ?? []), ...event.checks],
            suggestions: [
              ...(currentResult?.suggestions ?? []),
              ...event.suggestions,
            ],
            classification: event.classification,
          }));
          return;
        }

        if (event.type === "final") {
          setResult(event.result);
        }
      });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to validate story.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function loadExample(example: StoryValidationRequest) {
    setForm(example);
    setCriteriaText(listToText(example.acceptanceCriteria));
    setDependenciesText(listToText(example.dependencies));
    setResult(null);
    setError("");
  }

  return (
    <main className="app-shell">
      <section className="overview">
        <div>
          <p className="eyebrow">Story Analyzer</p>
          <h1>Validate story readiness before work starts.</h1>
          <p className="intro">
            Enter a story, validate it against delivery-readiness checks, and
            review the score, failed checks, and refinement suggestions.
          </p>
        </div>
        <div className="status-strip" aria-label="Validation summary">
          <div>
            <span>Score</span>
            <strong>{result ? result.score : "--"}</strong>
          </div>
          <div>
            <span>Status</span>
            <strong>{result ? result.status : "Not validated"}</strong>
          </div>
          <div>
            <span>Checks</span>
            <strong>
              {result ? `${passedChecks}/${result.checks.length}` : "--"}
            </strong>
          </div>
        </div>
      </section>

      <section className="workspace" aria-label="Story validation workspace">
        <form className="story-form" onSubmit={handleSubmit}>
          <div className="section-heading">
            <p className="eyebrow">Story input form</p>
            <h2>Story details</h2>
          </div>

          <label>
            <span>Title</span>
            <input
              value={form.title}
              onChange={(event) =>
                setForm({ ...form, title: event.target.value })
              }
              placeholder="Export readiness report"
            />
          </label>

          <label>
            <span>User story</span>
            <textarea
              className="story-textarea"
              value={form.story}
              onChange={(event) =>
                setForm({ ...form, story: event.target.value })
              }
              placeholder="As a product owner, I want..."
            />
          </label>

          <label>
            <span>Acceptance criteria</span>
            <textarea
              value={criteriaText}
              onChange={(event) => setCriteriaText(event.target.value)}
              placeholder="One criterion per line"
            />
          </label>

          <div className="field-grid">
            <label>
              <span>Priority</span>
              <select
                value={form.priority}
                onChange={(event) =>
                  setForm({ ...form, priority: event.target.value })
                }
              >
                <option value="">Select priority</option>
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
                <option>Critical</option>
              </select>
            </label>

            <label>
              <span>Estimate</span>
              <input
                value={form.estimate}
                onChange={(event) =>
                  setForm({ ...form, estimate: event.target.value })
                }
                placeholder="3"
              />
            </label>
          </div>

          <label>
            <span>Dependencies</span>
            <textarea
              value={dependenciesText}
              onChange={(event) => setDependenciesText(event.target.value)}
              placeholder="One dependency per line, or none"
            />
          </label>

          {error ? <p className="error-message">{error}</p> : null}

          <div className="form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Validating..." : "Validate Story"}
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setForm(emptyForm);
                setCriteriaText("");
                setDependenciesText("");
                setResult(null);
                setError("");
              }}
            >
              Reset
            </button>
          </div>
        </form>

        <div className="results-column">
          <section className="results-panel">
            <div className="section-heading">
              <p className="eyebrow">Validation results panel</p>
              <h2>{result ? result.status : "Awaiting validation"}</h2>
            </div>
            {result ? (
              <>
                <div className="score-row">
                  <div
                    className="score-ring"
                    style={
                      {
                        "--score": `${result.score}%`,
                      } as React.CSSProperties
                    }
                    aria-label={`Score ${result.score}`}
                  >
                    <span>{result.score}</span>
                  </div>
                  <div>
                    <p className="result-label">
                      {result.readyForWork ? "Ready for work" : "Needs work"}
                    </p>
                    <p className="muted">
                      {failedChecks.length
                        ? `${failedChecks.length} checks need attention.`
                        : "All readiness checks passed."}
                    </p>
                  </div>
                </div>

                <div className="check-list" aria-label="Score breakdown">
                  <h3>Score breakdown</h3>
                  {result.checks.map((check) => (
                    <div className="check-item" key={check.name}>
                      <span
                        className={check.passed ? "pass-dot" : "fail-dot"}
                        aria-hidden="true"
                      />
                      <span>{check.message}</span>
                    </div>
                  ))}
                </div>

                {result.classification ? (
                  <div className="classification-panel">
                    <h3>Hugging Face classification</h3>
                    <div>
                      <span>Label</span>
                      <strong>{result.classification.label}</strong>
                    </div>
                    <div>
                      <span>Confidence</span>
                      <strong>
                        {Math.round(result.classification.confidence * 100)}%
                      </strong>
                    </div>
                    <div>
                      <span>Model</span>
                      <strong>{result.classification.model}</strong>
                    </div>
                    <div className="classification-scores">
                      <span>Label scores</span>
                      {classificationScores.map(([label, score]) => (
                        <p key={label}>
                          <span>{label}</span>
                          <strong>{Math.round(score * 100)}%</strong>
                        </p>
                      ))}
                    </div>
                  </div>
                ) : null}
              </>
            ) : (
              <p className="muted">
                Submit a story to see the pass/fail status and score breakdown.
              </p>
            )}
          </section>

          <section className="suggestions-panel">
            <div className="section-heading">
              <p className="eyebrow">Suggestion list</p>
              <h2>Refinement suggestions</h2>
            </div>
            {result?.suggestions.length ? (
              <ul>
                {result.suggestions.map((suggestion) => (
                  <li key={suggestion}>{suggestion}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                Suggestions will appear here when checks fail.
              </p>
            )}
          </section>

          <section className="examples-panel">
            <div className="section-heading">
              <p className="eyebrow">Example stories</p>
              <h2>Load a sample</h2>
            </div>
            <div className="example-list">
              {exampleStories.map((example) => (
                <button
                  className="example-button"
                  key={example.title}
                  type="button"
                  onClick={() => loadExample(example)}
                >
                  <strong>{example.title}</strong>
                  <span>{example.priority} priority</span>
                </button>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
