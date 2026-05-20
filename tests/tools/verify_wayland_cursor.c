#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <wayland-client.h>
#include <wayland-cursor.h>

static struct wl_shm *shm = NULL;

static void registry_global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version) {
    (void)data;
    (void)version;

    if (strcmp(interface, "wl_shm") == 0) {
        shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
    }
}

static void registry_remove(void *data, struct wl_registry *registry, uint32_t name) {
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {
    registry_global,
    registry_remove,
};

static int should_check_exact_size(const char *name) {
    return strcmp(name, "left_ptr") == 0 || strcmp(name, "default") == 0 || strcmp(name, "watch") == 0;
}

int main(int argc, char **argv) {
    const char *theme_name = argc > 1 ? argv[1] : NULL;
    int size = argc > 2 ? atoi(argv[2]) : 32;
    int expected_size = argc > 3 ? atoi(argv[3]) : 0;
    const char *names[] = {
        "left_ptr",
        "default",
        "wayland-cursor",
        "text",
        "hand2",
        "watch",
        "crosshair",
        "move",
        "sb_h_double_arrow",
        "sb_v_double_arrow",
        "zoom-in",
        "zoom-out",
    };

    struct wl_display *display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "failed to connect Wayland display\n");
        return 1;
    }

    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    if (wl_display_roundtrip(display) < 0) {
        fprintf(stderr, "failed to roundtrip Wayland registry\n");
        wl_registry_destroy(registry);
        wl_display_disconnect(display);
        return 1;
    }

    if (!shm) {
        fprintf(stderr, "wl_shm is not available\n");
        wl_registry_destroy(registry);
        wl_display_disconnect(display);
        return 1;
    }

    struct wl_cursor_theme *theme = wl_cursor_theme_load(theme_name, size, shm);
    if (!theme) {
        fprintf(stderr, "failed to load cursor theme: %s\n", theme_name ? theme_name : "(default)");
        wl_shm_destroy(shm);
        wl_registry_destroy(registry);
        wl_display_disconnect(display);
        return 1;
    }

    int failed = 0;
    for (size_t i = 0; i < sizeof(names) / sizeof(names[0]); i++) {
        struct wl_cursor *cursor = wl_cursor_theme_get_cursor(theme, names[i]);
        if (!cursor) {
            printf("MISSING %s\n", names[i]);
            failed = 1;
            continue;
        }

        printf("OK %s images=%u\n", names[i], cursor->image_count);
        int found_expected_size = expected_size <= 0 || !should_check_exact_size(names[i]);
        for (uint32_t j = 0; j < cursor->image_count; j++) {
            struct wl_cursor_image *image = cursor->images[j];
            struct wl_buffer *buffer = wl_cursor_image_get_buffer(image);
            if (!buffer) {
                printf("  BUFFER_FAIL frame=%u\n", j);
                failed = 1;
                continue;
            }

            printf(
                "  frame=%u size=%ux%u hotspot=%u,%u delay=%u\n",
                j,
                image->width,
                image->height,
                image->hotspot_x,
                image->hotspot_y,
                image->delay
            );
            if ((uint32_t)expected_size == image->width && (uint32_t)expected_size == image->height) {
                found_expected_size = 1;
            }
        }

        if (!found_expected_size) {
            printf("  SIZE_MISMATCH expected=%d\n", expected_size);
            failed = 1;
        }
    }

    wl_cursor_theme_destroy(theme);
    wl_shm_destroy(shm);
    wl_registry_destroy(registry);
    wl_display_disconnect(display);

    return failed;
}
