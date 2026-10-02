package org.tripsphere.inventory.infrastructure.observability;

import io.grpc.Context;
import io.grpc.Metadata;
import java.util.UUID;
import org.slf4j.MDC;

public final class CorrelationContext {

    public static final Metadata.Key<String> REQUEST_ID_METADATA_KEY =
            Metadata.Key.of("x-request-id", Metadata.ASCII_STRING_MARSHALLER);

    private static final Context.Key<String> REQUEST_ID_CONTEXT_KEY = Context.key("request-id");
    private static final String REQUEST_ID_MDC_KEY = "request.id";
    private static final String REQUEST_ID_ALIAS_MDC_KEY = "request_id";
    private static final int MAX_REQUEST_ID_LENGTH = 128;

    private CorrelationContext() {}

    public static String requestIdFromMetadata(Metadata metadata) {
        return normalize(metadata == null ? null : metadata.get(REQUEST_ID_METADATA_KEY));
    }

    public static Context attach(Context context, String requestId) {
        return context.withValue(REQUEST_ID_CONTEXT_KEY, normalize(requestId));
    }

    public static Scope openMdc(String requestId) {
        String normalizedRequestId = normalize(requestId);
        Context previousContext = Context.current();
        Context attachedContext = previousContext.withValue(REQUEST_ID_CONTEXT_KEY, normalizedRequestId);
        Context previousAttachedContext = attachedContext.attach();

        String previousMdcRequestId = MDC.get(REQUEST_ID_MDC_KEY);
        String previousMdcRequestIdAlias = MDC.get(REQUEST_ID_ALIAS_MDC_KEY);
        MDC.put(REQUEST_ID_MDC_KEY, normalizedRequestId);
        MDC.put(REQUEST_ID_ALIAS_MDC_KEY, normalizedRequestId);

        return new Scope(
                attachedContext,
                previousAttachedContext,
                previousMdcRequestId,
                previousMdcRequestIdAlias);
    }

    private static String normalize(String requestId) {
        if (requestId == null) {
            return UUID.randomUUID().toString();
        }

        String value = requestId.trim();
        if (value.isEmpty() || value.length() > MAX_REQUEST_ID_LENGTH) {
            return UUID.randomUUID().toString();
        }
        if (value.chars().anyMatch(Character::isISOControl)) {
            return UUID.randomUUID().toString();
        }
        return value;
    }

    public static final class Scope implements AutoCloseable {
        private final Context attachedContext;
        private final Context previousContext;
        private final String previousMdcRequestId;
        private final String previousMdcRequestIdAlias;

        private Scope(
                Context attachedContext,
                Context previousContext,
                String previousMdcRequestId,
                String previousMdcRequestIdAlias) {
            this.attachedContext = attachedContext;
            this.previousContext = previousContext;
            this.previousMdcRequestId = previousMdcRequestId;
            this.previousMdcRequestIdAlias = previousMdcRequestIdAlias;
        }

        @Override
        public void close() {
            restoreMdc(REQUEST_ID_MDC_KEY, previousMdcRequestId);
            restoreMdc(REQUEST_ID_ALIAS_MDC_KEY, previousMdcRequestIdAlias);
            attachedContext.detach(previousContext);
        }

        private static void restoreMdc(String key, String value) {
            if (value == null) {
                MDC.remove(key);
            } else {
                MDC.put(key, value);
            }
        }
    }
}
