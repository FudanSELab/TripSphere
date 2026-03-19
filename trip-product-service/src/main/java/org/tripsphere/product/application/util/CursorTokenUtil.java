package org.tripsphere.product.application.util;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

public class CursorTokenUtil {
    public record CursorToken(String id) {
        public CursorToken {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("ID cannot be null or blank");
            }
        }
    }

    public static String encode(CursorToken cursorToken) {
        if (cursorToken == null) {
            throw new IllegalArgumentException("Cursor token is required");
        }

        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(cursorToken.id().getBytes(StandardCharsets.UTF_8));
    }

    public static CursorToken decode(String pageToken) {
        if (pageToken == null || pageToken.isEmpty()) {
            throw new IllegalArgumentException("Page token is required");
        }

        try {
            byte[] decodedBytes = Base64.getUrlDecoder().decode(pageToken);
            String id = new String(decodedBytes, StandardCharsets.UTF_8);
            return new CursorToken(id);
        } catch (Exception e) {
            throw new IllegalArgumentException("Failed to decode page token: " + pageToken, e);
        }
    }
}
