package org.tripsphere.user.grpc;

import io.grpc.Context;

/**
 * Context keys for storing user information in gRPC context
 */
public class ContextKeys {
    /**
     * Context key for storing username
     */
    public static final Context.Key<String> USERNAME_KEY = Context.key("username");
    
    private ContextKeys() {
        // Utility class
    }
}

