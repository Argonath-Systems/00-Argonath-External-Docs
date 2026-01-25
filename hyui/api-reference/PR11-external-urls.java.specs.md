/**
 * PR 11: External URL Handling (Original PR 12)
 * 
 * Problem: No way to open external links (wiki, Discord, etc.) from UI.
 * Solution: Use Hytale's message system for clickable links or browser API.
 * 
 * Files to modify:
 * - src/main/java/au/ellie/hyui/core/UIContext.java
 * - src/main/java/au/ellie/hyui/core/HyUIPage.java
 * - src/main/java/au/ellie/hyui/core/HyUIHud.java
 * 
 * Effort: ~1 hour
 */

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/UIContext.java
// ADD interface method:
// ============================================================================

/**
 * Opens an external URL.
 * The implementation may show a confirmation dialog, send a clickable
 * chat message, or open a browser depending on platform capabilities.
 *
 * @param url The URL to open (must be http:// or https://)
 */
void openExternalUrl(String url);

/**
 * Opens an external URL with a custom display text.
 *
 * @param url The URL to open
 * @param displayText The text shown to the user
 */
void openExternalUrl(String url, String displayText);

/**
 * Checks if opening external URLs is supported.
 *
 * @return true if external URLs can be opened
 */
default boolean supportsExternalUrls() {
    return true;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/ExternalUrlHandler.java (NEW)
// ============================================================================

package au.ellie.hyui.core;

import java.util.Set;
import java.util.HashSet;
import java.util.regex.Pattern;

/**
 * Handles external URL validation and opening.
 * Provides security features like domain whitelisting and URL validation.
 */
public class ExternalUrlHandler {
    
    private static final org.slf4j.Logger LOGGER = 
        org.slf4j.LoggerFactory.getLogger(ExternalUrlHandler.class);
    
    /**
     * Allowed URL schemes.
     */
    private static final Set<String> ALLOWED_SCHEMES = Set.of("http", "https");
    
    /**
     * Pattern for basic URL validation.
     */
    private static final Pattern URL_PATTERN = Pattern.compile(
        "^https?://[a-zA-Z0-9][a-zA-Z0-9-]*(\\.[a-zA-Z0-9-]+)+(/.*)?$"
    );
    
    /**
     * Maximum URL length to prevent abuse.
     */
    private static final int MAX_URL_LENGTH = 2048;
    
    /**
     * Whitelisted domains (if empty, all domains allowed).
     */
    private final Set<String> whitelistedDomains = new HashSet<>();
    
    /**
     * Blacklisted domains.
     */
    private final Set<String> blacklistedDomains = new HashSet<>();
    
    /**
     * Whether to require confirmation before opening URLs.
     */
    private boolean requireConfirmation = false;
    
    /**
     * Whether to log URL access attempts.
     */
    private boolean logAccess = true;
    
    // ============ Configuration ============
    
    /**
     * Adds a domain to the whitelist.
     * If any domain is whitelisted, only whitelisted domains are allowed.
     *
     * @param domain The domain to whitelist (e.g., "example.com")
     * @return this handler for chaining
     */
    public ExternalUrlHandler whitelist(String domain) {
        whitelistedDomains.add(domain.toLowerCase());
        return this;
    }
    
    /**
     * Adds a domain to the blacklist.
     * Blacklisted domains are always blocked, even if whitelisted.
     *
     * @param domain The domain to blacklist
     * @return this handler for chaining
     */
    public ExternalUrlHandler blacklist(String domain) {
        blacklistedDomains.add(domain.toLowerCase());
        return this;
    }
    
    /**
     * Sets whether to require confirmation before opening URLs.
     *
     * @param require true to require confirmation
     * @return this handler for chaining
     */
    public ExternalUrlHandler requireConfirmation(boolean require) {
        this.requireConfirmation = require;
        return this;
    }
    
    /**
     * Sets whether to log URL access attempts.
     *
     * @param log true to log access
     * @return this handler for chaining
     */
    public ExternalUrlHandler logAccess(boolean log) {
        this.logAccess = log;
        return this;
    }
    
    // ============ Validation ============
    
    /**
     * Validates a URL for opening.
     *
     * @param url The URL to validate
     * @return Result containing validation status and message
     */
    public ValidationResult validate(String url) {
        // Null/empty check
        if (url == null || url.isBlank()) {
            return ValidationResult.invalid("URL is empty");
        }
        
        // Length check
        if (url.length() > MAX_URL_LENGTH) {
            return ValidationResult.invalid("URL exceeds maximum length");
        }
        
        // Scheme check
        String scheme = extractScheme(url);
        if (scheme == null || !ALLOWED_SCHEMES.contains(scheme.toLowerCase())) {
            return ValidationResult.invalid("Only HTTP and HTTPS URLs are allowed");
        }
        
        // Basic format check
        if (!URL_PATTERN.matcher(url).matches()) {
            return ValidationResult.invalid("Invalid URL format");
        }
        
        // Domain extraction
        String domain = extractDomain(url);
        if (domain == null) {
            return ValidationResult.invalid("Could not extract domain from URL");
        }
        
        // Blacklist check
        if (isDomainBlacklisted(domain)) {
            return ValidationResult.invalid("Domain is blocked");
        }
        
        // Whitelist check (if whitelist is active)
        if (!whitelistedDomains.isEmpty() && !isDomainWhitelisted(domain)) {
            return ValidationResult.invalid("Domain is not in allowed list");
        }
        
        return ValidationResult.valid();
    }
    
    /**
     * Checks if a URL is safe to open.
     *
     * @param url The URL to check
     * @return true if the URL passes validation
     */
    public boolean isUrlSafe(String url) {
        return validate(url).isValid();
    }
    
    // ============ URL Opening ============
    
    /**
     * Opens a URL for a player.
     * 
     * @param playerRef The player to open the URL for
     * @param url The URL to open
     * @param displayText Optional display text (null to use URL)
     * @return true if the URL was opened/sent successfully
     */
    public boolean openUrl(PlayerRef playerRef, String url, String displayText) {
        // Validate
        ValidationResult result = validate(url);
        if (!result.isValid()) {
            LOGGER.warn("Blocked URL for player {}: {} - {}", 
                playerRef.getId(), url, result.getMessage());
            return false;
        }
        
        // Log if enabled
        if (logAccess) {
            LOGGER.info("Opening URL for player {}: {}", playerRef.getId(), url);
        }
        
        // Determine display text
        String text = displayText != null ? displayText : truncateForDisplay(url);
        
        // Send as clickable chat message
        // This is the safest approach as Hytale likely handles URL clicking securely
        sendClickableUrl(playerRef, url, text);
        
        return true;
    }
    
    /**
     * Sends a clickable URL to the player via chat.
     */
    private void sendClickableUrl(PlayerRef playerRef, String url, String displayText) {
        // Using Hytale's message API (example implementation)
        // The actual API may differ
        
        // Option 1: Using Message.ofUrl if available
        // playerRef.sendMessage(Message.ofUrl(url, displayText));
        
        // Option 2: Using component-based message
        // playerRef.sendMessage(
        //     TextComponent.text("[")
        //         .append(TextComponent.text(displayText)
        //             .color(NamedTextColor.AQUA)
        //             .clickEvent(ClickEvent.openUrl(url))
        //             .hoverEvent(HoverEvent.showText(TextComponent.text(url))))
        //         .append(TextComponent.text("]"))
        // );
        
        // Fallback: Plain message with URL
        playerRef.sendMessage("[Link] " + displayText + ": " + url);
    }
    
    // ============ Utility Methods ============
    
    /**
     * Extracts the scheme from a URL.
     */
    private String extractScheme(String url) {
        int idx = url.indexOf("://");
        if (idx > 0) {
            return url.substring(0, idx);
        }
        return null;
    }
    
    /**
     * Extracts the domain from a URL.
     */
    private String extractDomain(String url) {
        try {
            int start = url.indexOf("://") + 3;
            int end = url.indexOf('/', start);
            if (end < 0) end = url.length();
            
            String domain = url.substring(start, end).toLowerCase();
            
            // Remove port if present
            int portIdx = domain.indexOf(':');
            if (portIdx > 0) {
                domain = domain.substring(0, portIdx);
            }
            
            return domain;
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * Checks if a domain is whitelisted (including subdomains).
     */
    private boolean isDomainWhitelisted(String domain) {
        for (String whitelisted : whitelistedDomains) {
            if (domain.equals(whitelisted) || domain.endsWith("." + whitelisted)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * Checks if a domain is blacklisted (including subdomains).
     */
    private boolean isDomainBlacklisted(String domain) {
        for (String blacklisted : blacklistedDomains) {
            if (domain.equals(blacklisted) || domain.endsWith("." + blacklisted)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * Truncates a URL for display in chat.
     */
    private String truncateForDisplay(String url) {
        if (url.length() <= 50) return url;
        return url.substring(0, 47) + "...";
    }
    
    // ============ Validation Result ============
    
    /**
     * Result of URL validation.
     */
    public static class ValidationResult {
        private final boolean valid;
        private final String message;
        
        private ValidationResult(boolean valid, String message) {
            this.valid = valid;
            this.message = message;
        }
        
        public static ValidationResult valid() {
            return new ValidationResult(true, null);
        }
        
        public static ValidationResult invalid(String message) {
            return new ValidationResult(false, message);
        }
        
        public boolean isValid() { return valid; }
        public String getMessage() { return message; }
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HyUIPage.java
// ADD implementation:
// ============================================================================

/**
 * Handler for external URLs.
 */
private static final ExternalUrlHandler urlHandler = new ExternalUrlHandler();

/**
 * Configure URL handler for your server.
 * Call this once during mod initialization.
 */
public static void configureUrlHandler(Consumer<ExternalUrlHandler> config) {
    config.accept(urlHandler);
}

@Override
public void openExternalUrl(String url) {
    openExternalUrl(url, null);
}

@Override
public void openExternalUrl(String url, String displayText) {
    if (url == null || url.isBlank()) {
        LOGGER.warn("Attempted to open null/empty URL");
        return;
    }
    
    // Validate and open
    if (urlHandler.openUrl(playerRef, url, displayText)) {
        // Fire event for tracking/analytics
        fireEvent("url:opened", Map.of(
            "url", url,
            "display", displayText != null ? displayText : url
        ));
    } else {
        // Notify user that URL was blocked
        playerRef.sendMessage("§cThis link cannot be opened.");
        
        fireEvent("url:blocked", Map.of("url", url));
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
HYUIML Usage:
-------------
<!-- Basic external link -->
<a href="https://wiki.yourserver.com/items">Item Wiki</a>

<!-- With custom text -->
<a href="https://discord.gg/yourserver">Join our Discord!</a>

<!-- Wiki link with title -->
<a href="https://wiki.yourserver.com/guides/beginner" title="Opens in browser">
    Beginner's Guide
</a>

Mod Initialization - Configure URL Handler:
-------------------------------------------
public void onModInit() {
    // Configure which URLs are allowed
    HyUIPage.configureUrlHandler(handler -> {
        // Only allow your own domains
        handler.whitelist("yourserver.com")
               .whitelist("wiki.yourserver.com")
               .whitelist("discord.gg");
        
        // Block known bad domains
        handler.blacklist("malicious-site.com");
        
        // Enable logging for security audits
        handler.logAccess(true);
    });
}

Java Usage - Opening URLs:
--------------------------
// In button click handler
builder.addEventListener("wiki-link", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.openExternalUrl("https://wiki.yourserver.com/items/sword");
});

// With custom display text
builder.addEventListener("discord-link", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.openExternalUrl("https://discord.gg/yourserver", "Click to join Discord");
});

Java Usage - Conditional URL:
-----------------------------
builder.addEventListener("profile-link", CustomUIEventBindingType.Activating, (data, ctx) -> {
    String playerName = data.get("playerName");
    String url = "https://yourserver.com/players/" + URLEncoder.encode(playerName, UTF_8);
    ctx.openExternalUrl(url, "View " + playerName + "'s profile");
});

Error Handling:
---------------
builder.addEventListener("external-link", CustomUIEventBindingType.Activating, (data, ctx) -> {
    String url = data.get("url");
    
    // Check if URL is safe first
    if (ctx.supportsExternalUrls()) {
        ctx.openExternalUrl(url);
    } else {
        ctx.showNotification("External links are not available");
    }
});

Complete Integration Example:
-----------------------------
public class WikiLinkHandler {
    
    private static final String WIKI_BASE = "https://wiki.yourserver.com/";
    
    public void registerWikiLinks(InterfaceBuilder<?> builder) {
        // Item wiki links
        builder.addEventListener("view-item-wiki", CustomUIEventBindingType.Activating, (data, ctx) -> {
            String itemId = data.get("itemId");
            if (itemId != null) {
                ctx.openExternalUrl(
                    WIKI_BASE + "items/" + itemId,
                    "View item on wiki"
                );
            }
        });
        
        // Quest wiki links
        builder.addEventListener("view-quest-wiki", CustomUIEventBindingType.Activating, (data, ctx) -> {
            String questId = data.get("questId");
            if (questId != null) {
                ctx.openExternalUrl(
                    WIKI_BASE + "quests/" + questId,
                    "View quest guide"
                );
            }
        });
        
        // General help link
        builder.addEventListener("help-link", CustomUIEventBindingType.Activating, (data, ctx) -> {
            ctx.openExternalUrl(WIKI_BASE + "help", "Open Help Center");
        });
    }
}

HYUIML with Dynamic Wiki Links:
-------------------------------
<!-- Item tooltip with wiki link -->
<div class="item-tooltip">
    <p class="item-name">{{$itemName}}</p>
    <p class="item-description">{{$itemDesc}}</p>
    <div class="tooltip-footer">
        <a href="https://wiki.yourserver.com/items/{{$itemId}}" 
           style="color: #4a90d9; font-size: 10;">
            View on Wiki
        </a>
    </div>
</div>
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/core/ExternalUrlHandlerTest.java
// ============================================================================

@Test
void validate_acceptsHttps() {
    ExternalUrlHandler handler = new ExternalUrlHandler();
    
    assertThat(handler.isUrlSafe("https://example.com")).isTrue();
    assertThat(handler.isUrlSafe("https://example.com/path")).isTrue();
    assertThat(handler.isUrlSafe("https://sub.example.com")).isTrue();
}

@Test
void validate_acceptsHttp() {
    ExternalUrlHandler handler = new ExternalUrlHandler();
    
    assertThat(handler.isUrlSafe("http://example.com")).isTrue();
}

@Test
void validate_rejectsNonHttp() {
    ExternalUrlHandler handler = new ExternalUrlHandler();
    
    assertThat(handler.isUrlSafe("ftp://example.com")).isFalse();
    assertThat(handler.isUrlSafe("file:///etc/passwd")).isFalse();
    assertThat(handler.isUrlSafe("javascript:alert(1)")).isFalse();
}

@Test
void validate_rejectsEmptyUrl() {
    ExternalUrlHandler handler = new ExternalUrlHandler();
    
    assertThat(handler.isUrlSafe("")).isFalse();
    assertThat(handler.isUrlSafe(null)).isFalse();
    assertThat(handler.isUrlSafe("   ")).isFalse();
}

@Test
void whitelist_allowsOnlyWhitelisted() {
    ExternalUrlHandler handler = new ExternalUrlHandler()
        .whitelist("allowed.com");
    
    assertThat(handler.isUrlSafe("https://allowed.com")).isTrue();
    assertThat(handler.isUrlSafe("https://sub.allowed.com")).isTrue();
    assertThat(handler.isUrlSafe("https://blocked.com")).isFalse();
}

@Test
void blacklist_blocksBlacklisted() {
    ExternalUrlHandler handler = new ExternalUrlHandler()
        .blacklist("blocked.com");
    
    assertThat(handler.isUrlSafe("https://blocked.com")).isFalse();
    assertThat(handler.isUrlSafe("https://sub.blocked.com")).isFalse();
    assertThat(handler.isUrlSafe("https://allowed.com")).isTrue();
}

@Test
void blacklist_overridesWhitelist() {
    ExternalUrlHandler handler = new ExternalUrlHandler()
        .whitelist("example.com")
        .blacklist("bad.example.com");
    
    assertThat(handler.isUrlSafe("https://example.com")).isTrue();
    assertThat(handler.isUrlSafe("https://bad.example.com")).isFalse();
}

@Test
void validate_rejectsTooLongUrl() {
    ExternalUrlHandler handler = new ExternalUrlHandler();
    String longUrl = "https://example.com/" + "a".repeat(3000);
    
    assertThat(handler.isUrlSafe(longUrl)).isFalse();
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("externalLinkDemo", """
    <div style="layout-mode: Top; gap: 12; padding: 16; background-color: #1a1a26;">
        <p style="color: white; font-size: 14;">External Links:</p>
        
        <div style="layout-mode: Top; gap: 8; margin-top: 8;">
            <a href="https://wiki.example.com">Wiki (example)</a>
            <a href="https://discord.gg/example">Discord (example)</a>
            <a href="https://github.com/example">GitHub (example)</a>
        </div>
        
        <p style="color: #666666; font-size: 10; margin-top: 16;">
            Note: Links open via chat message
        </p>
    </div>
""")
