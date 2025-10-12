// EvoVision Dashboard persistence helpers with resilient fallback.

async function persistToDirectory(event) {
  if (!window.showSaveFilePicker) {
    throw new Error("File System Access API unavailable");
  }
  const handle = await window.showSaveFilePicker({
    suggestedName: `evo-vision-${Date.now()}.json`,
    types: [
      {
        description: "EvoVision Event",
        accept: { "application/json": [".json"] },
      },
    ],
  });
  const writable = await handle.createWritable();
  await writable.write(JSON.stringify(event, null, 2));
  await writable.close();
}

// Resilient persistence routine that falls back to localStorage on failure.
export async function persistEvent(event) {
  try {
    await persistToDirectory(event);
  } catch (error) {
    console.error("[EvoVisionDashboard] Primary persistence failed:", error);
    try {
      const key = "EvoVisionFallback";
      const existing = JSON.parse(localStorage.getItem(key) || "[]");
      existing.push(event);
      localStorage.setItem(key, JSON.stringify(existing));
      console.warn("[EvoVisionDashboard] Event stored in localStorage fallback.");
    } catch (fallbackError) {
      console.error("[EvoVisionDashboard] Fallback persistence failed:", fallbackError);
      alert("⚠️ Не удалось сохранить событие — проверьте доступ к EVO-папке.");
    }
  }
}
