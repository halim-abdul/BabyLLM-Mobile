package org.babyllm.mobile;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import java.util.Arrays;

public final class TokenizationTest {
    @Test public void unicodeWordsAndPunctuation() {
        assertEquals(Arrays.asList("Hola", ",", "世界", "!", "café"),
                Tokenization.tokens("Hola, 世界! café"));
    }

    @Test public void continuationSpacing() {
        assertEquals("hello, world!", Tokenization.join(Arrays.asList("hello", ",", "world", "!")));
    }
}
