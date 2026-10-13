package org.babyllm.mobile;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONArray;

import java.util.ArrayList;
import java.util.List;

final class MemoryStore extends SQLiteOpenHelper {
    private static final int ORDER = 3;
    private static final String START = "<s>";
    private static final String END = "</s>";

    MemoryStore(Context context) {
        super(context, "babyllm.sqlite3", null, 1);
    }

    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE grams (context TEXT NOT NULL, token TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(context, token))");
        db.execSQL("CREATE TABLE documents (id TEXT PRIMARY KEY, token_count INTEGER NOT NULL)");
    }

    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        throw new IllegalStateException("No database migration is available");
    }

    int learn(String text, String documentId) {
        List<String> tokens = Tokenization.tokens(text);
        if (tokens.isEmpty()) return 0;
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            if (documentId != null) {
                ContentValues document = new ContentValues();
                document.put("id", documentId);
                document.put("token_count", tokens.size());
                if (db.insertWithOnConflict("documents", null, document, SQLiteDatabase.CONFLICT_IGNORE) == -1) {
                    db.setTransactionSuccessful();
                    return 0;
                }
            }
            List<String> sequence = new ArrayList<>();
            sequence.add(START);
            sequence.add(START);
            sequence.addAll(tokens);
            sequence.add(END);
            for (int i = ORDER - 1; i < sequence.size(); i++) {
                for (int width = 0; width < ORDER; width++) {
                    String context = key(sequence.subList(i - width, i));
                    String token = sequence.get(i);
                    ContentValues values = new ContentValues();
                    values.put("context", context);
                    values.put("token", token);
                    values.put("n", 1);
                    long inserted = db.insertWithOnConflict("grams", null, values, SQLiteDatabase.CONFLICT_IGNORE);
                    if (inserted == -1) {
                        db.execSQL("UPDATE grams SET n=n+1 WHERE context=? AND token=?", new Object[]{context, token});
                    }
                }
            }
            db.setTransactionSuccessful();
            return tokens.size();
        } finally {
            db.endTransaction();
        }
    }

    String complete(String prompt, int maxTokens) {
        List<String> context = new ArrayList<>();
        context.add(START);
        context.add(START);
        context.addAll(Tokenization.tokens(prompt));
        List<String> output = new ArrayList<>();
        for (int i = 0; i < maxTokens; i++) {
            String next = next(context);
            if (next == null || END.equals(next)) break;
            output.add(next);
            context.add(next);
        }
        return Tokenization.join(output);
    }

    private String next(List<String> context) {
        SQLiteDatabase db = getReadableDatabase();
        for (int width = Math.min(ORDER - 1, context.size()); width >= 0; width--) {
            String key = key(context.subList(context.size() - width, context.size()));
            try (Cursor cursor = db.rawQuery(
                    "SELECT token FROM grams WHERE context=? ORDER BY n DESC, token LIMIT 1",
                    new String[]{key})) {
                if (cursor.moveToFirst()) return cursor.getString(0);
            }
        }
        return null;
    }

    String stats() {
        SQLiteDatabase db = getReadableDatabase();
        try (Cursor cursor = db.rawQuery("SELECT COUNT(*) FROM grams", null)) {
            cursor.moveToFirst();
            return "Distinct n-grams: " + cursor.getLong(0);
        }
    }

    void clearAll() {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            db.delete("grams", null, null);
            db.delete("documents", null, null);
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }

    private static String key(List<String> context) {
        return new JSONArray(context).toString();
    }
}
