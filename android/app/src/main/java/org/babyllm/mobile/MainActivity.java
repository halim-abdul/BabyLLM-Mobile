package org.babyllm.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final int PICK_TEXT = 1;
    private static final int MAX_FILE_BYTES = 1024 * 1024;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private MemoryStore memory;
    private EditText input;
    private TextView output;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        memory = new MemoryStore(this);

        ScrollView scroll = new ScrollView(this);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (16 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, pad);
        scroll.addView(layout);

        TextView title = new TextView(this);
        title.setText("BabyLLM research prototype");
        title.setTextSize(22);
        layout.addView(title);
        TextView description = new TextView(this);
        description.setText("Offline n-gram continuation. Add text explicitly; results are not verified answers.");
        layout.addView(description);

        input = new EditText(this);
        input.setHint("Enter text to learn or a prompt to continue");
        input.setMinLines(3);
        input.setGravity(android.view.Gravity.TOP);
        layout.addView(input);

        button(layout, "Learn entered text", view -> {
            String text = input.getText().toString();
            if (text.trim().isEmpty()) { output.setText("Enter some text first."); return; }
            runTask(() -> "Learned " + memory.learn(text, null) + " tokens. " + memory.stats());
        });
        button(layout, "Continue prompt", view -> {
            String prompt = input.getText().toString();
            runTask(() -> {
                String result = memory.complete(prompt, 30);
                return result.isEmpty() ? "No continuation in memory yet." : result;
            });
        });
        button(layout, "Import text file", view -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("text/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(intent, PICK_TEXT);
        });
        button(layout, "Memory size", view -> runTask(memory::stats));
        button(layout, "Clear all memory", view -> new AlertDialog.Builder(this)
                .setTitle("Delete learned memory?")
                .setMessage("This removes all local n-gram counts and imported document records.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Delete", (dialog, which) -> runTask(() -> {
                    memory.clearAll();
                    return "Local memory deleted.";
                })).show());

        output = new TextView(this);
        output.setText("Ready. Nothing is uploaded.");
        output.setTextIsSelectable(true);
        layout.addView(output);
        setContentView(scroll);
    }

    private void button(LinearLayout layout, String label, View.OnClickListener action) {
        Button button = new Button(this);
        button.setText(label);
        button.setOnClickListener(action);
        layout.addView(button);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_TEXT || resultCode != RESULT_OK || data == null || data.getData() == null) return;
        android.net.Uri uri = data.getData();
        runTask(() -> {
            byte[] bytes;
            try (InputStream stream = getContentResolver().openInputStream(uri)) {
                if (stream == null) throw new IllegalArgumentException("Document could not be opened");
                ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                byte[] chunk = new byte[8192];
                int read;
                while ((read = stream.read(chunk)) != -1) {
                    if (buffer.size() + read > MAX_FILE_BYTES) throw new IllegalArgumentException("File exceeds 1 MiB limit");
                    buffer.write(chunk, 0, read);
                }
                bytes = buffer.toByteArray();
            }
            String text = new String(bytes, StandardCharsets.UTF_8);
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            StringBuilder hex = new StringBuilder();
            for (byte value : digest) hex.append(String.format(java.util.Locale.ROOT, "%02x", value & 0xff));
            int count = memory.learn(text, hex.toString());
            return count == 0 ? "No new text learned (empty or previously imported)." : "Imported " + count + " tokens. " + memory.stats();
        });
    }

    private void runTask(Callable<String> task) {
        output.setText("Working…");
        worker.execute(() -> {
            String result;
            try {
                result = task.call();
            } catch (Exception error) {
                result = "Could not complete: " + error.getMessage();
            }
            String message = result;
            runOnUiThread(() -> { if (!isFinishing() && !isDestroyed()) output.setText(message); });
        });
    }

    @Override protected void onDestroy() {
        worker.shutdown();
        super.onDestroy();
    }
}
