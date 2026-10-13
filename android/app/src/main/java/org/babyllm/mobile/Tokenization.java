package org.babyllm.mobile;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class Tokenization {
    private static final Pattern TOKEN = Pattern.compile("[\\p{L}\\p{M}\\p{N}_]+|[^\\s]");

    private Tokenization() {}

    static List<String> tokens(String text) {
        Matcher matcher = TOKEN.matcher(text);
        List<String> result = new ArrayList<>();
        while (matcher.find()) result.add(matcher.group());
        return result;
    }

    static String join(List<String> tokens) {
        StringBuilder result = new StringBuilder();
        for (String token : tokens) {
            if (result.length() > 0 && !(token.length() == 1 && ".,!?;:%)]}".contains(token))) result.append(' ');
            result.append(token);
        }
        return result.toString();
    }
}
