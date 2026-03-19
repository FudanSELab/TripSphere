package org.tripsphere.user.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.Date;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

@Component
public class JwtUtil {

    @Value("${jwt.private-key}")
    private Resource privateKeyResource;

    @Value("${jwt.public-key}")
    private Resource publicKeyResource;

    @Value("${jwt.expiration:86400000}") // 24 hours
    private Long expiration;

    private PrivateKey privateKey;
    private JwtParser jwtParser;

    @PostConstruct
    public void init() {
        try {
            this.privateKey = loadPrivateKey(privateKeyResource);
            PublicKey publicKey = loadPublicKey(publicKeyResource);
            this.jwtParser = Jwts.parser().verifyWith(publicKey).build();
        } catch (Exception e) {
            throw new IllegalStateException("Failed to load RSA keys", e);
        }
    }

    private PrivateKey loadPrivateKey(Resource resource)
            throws IOException, NoSuchAlgorithmException, InvalidKeySpecException {
        String pem = readPem(resource);
        String base64 = pem.replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replace("-----BEGIN RSA PRIVATE KEY-----", "")
                .replace("-----END RSA PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        byte[] keyBytes = Base64.getDecoder().decode(base64);
        PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(keyBytes);
        return KeyFactory.getInstance("RSA").generatePrivate(keySpec);
    }

    private PublicKey loadPublicKey(Resource resource)
            throws IOException, NoSuchAlgorithmException, InvalidKeySpecException {
        String pem = readPem(resource);
        String base64 = pem.replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
        byte[] keyBytes = Base64.getDecoder().decode(base64);
        X509EncodedKeySpec keySpec = new X509EncodedKeySpec(keyBytes);
        return KeyFactory.getInstance("RSA").generatePublic(keySpec);
    }

    private String readPem(Resource resource) throws IOException {
        try (InputStream is = resource.getInputStream()) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    /**
     * Generate a JWT token with user ID as subject, and name, email, roles as claims.
     *
     * @param userId the user's unique ID (used as JWT subject)
     * @param name the user's display name
     * @param email the user's email address
     * @param roles the user's roles
     * @return signed JWT token string
     */
    public String generateToken(String userId, String name, String email, List<String> roles) {
        Date now = new Date();
        return Jwts.builder()
                .subject(userId)
                .claim("name", name)
                .claim("email", email)
                .claim("roles", roles)
                .issuedAt(now)
                .expiration(new Date(now.getTime() + expiration))
                .signWith(privateKey, Jwts.SIG.RS256)
                .compact();
    }

    /**
     * Parse and validate a JWT token in a single operation. Verifies the signature and checks
     * expiration, then extracts all claims at once — avoiding redundant parsing.
     *
     * @param token the raw JWT token string
     * @return parsed token claims
     * @throws JwtException if the token is invalid, expired, or has a bad signature
     */
    public TokenClaims parseAndValidate(String token) {
        Claims claims = jwtParser.parseSignedClaims(token).getPayload();
        return TokenClaims.from(claims);
    }

    /** Immutable holder for parsed JWT token claims. */
    public record TokenClaims(String userId, String name, String email, List<String> roles) {

        static TokenClaims from(Claims claims) {
            String userId = claims.getSubject();
            String name = claims.get("name", String.class);
            String email = claims.get("email", String.class);

            List<String> roles = List.of();
            Object rolesObj = claims.get("roles");
            if (rolesObj instanceof List<?> list) {
                roles = list.stream().map(Object::toString).toList();
            }

            return new TokenClaims(userId, name, email, roles);
        }
    }
}
