export type StoryValidationRequest = {
  title: string;
  story: string;
  acceptanceCriteria: string[];
  priority: string;
  estimate: string;
  dependencies: string[];
};

export type ValidationCheck = {
  name: string;
  passed: boolean;
  message: string;
};

export type StoryClassification = {
  label: string;
  confidence: number;
  scores: Record<string, number>;
  model: string;
};

export type StoryValidationResponse = {
  readyForWork: boolean;
  score: number;
  status: string;
  checks: ValidationCheck[];
  suggestions: string[];
  classification: StoryClassification | null;
};

export type StoryValidationStreamEvent =
  | {
      type: "rules_complete";
      checks: ValidationCheck[];
      suggestions: string[];
    }
  | {
      type: "ai_complete";
      checks: ValidationCheck[];
      suggestions: string[];
      classification: StoryClassification;
    }
  | {
      type: "final";
      result: StoryValidationResponse;
    }
  | {
      type: "error";
      message: string;
    };

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function validateStory(
  payload: StoryValidationRequest,
): Promise<StoryValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/validate-story`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const fallbackMessage = `Validation failed with status ${response.status}`;
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      typeof errorBody?.detail === "string" ? errorBody.detail : fallbackMessage,
    );
  }

  return response.json();
}

export async function validateStoryStream(
  payload: StoryValidationRequest,
  onEvent: (event: StoryValidationStreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/validate-story/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const fallbackMessage = `Validation failed with status ${response.status}`;
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      typeof errorBody?.detail === "string" ? errorBody.detail : fallbackMessage,
    );
  }

  if (!response.body) {
    throw new Error("Validation stream was not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let bufferedText = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    bufferedText += decoder.decode(value, { stream: true });
    const lines = bufferedText.split("\n");
    bufferedText = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }

      const event = JSON.parse(line) as StoryValidationStreamEvent;
      onEvent(event);

      if (event.type === "error") {
        throw new Error(event.message);
      }
    }
  }

  bufferedText += decoder.decode();
  if (bufferedText.trim()) {
    const event = JSON.parse(bufferedText) as StoryValidationStreamEvent;
    onEvent(event);

    if (event.type === "error") {
      throw new Error(event.message);
    }
  }
}
