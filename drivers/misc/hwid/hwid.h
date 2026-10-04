/* Stub for the stripped drivers/misc/hwid/ (Xiaomi OSS tree quirk). */
#ifndef _HWID_STUB_H
#define _HWID_STUB_H

enum country_version_stub {
    CountryCN = 100,
};

enum hardware_project_stub {
    HARDWARE_PROJECT_M2 = 101,
    HARDWARE_PROJECT_M3 = 102,
    HARDWARE_PROJECT_N11 = 103,
};

static inline int get_hw_version_platform(void) { return -1; }
static inline int get_hw_country_version(void) { return -1; }

#endif /* _HWID_STUB_H */
