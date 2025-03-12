#include <app_outage.h>


static uint32_t tick_zerocross=0;

static void cb_zerocross() {
    tick_zerocross = driver_rp2_get_global_tick();
}

void app_outage_init(app_outage_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_input(dev->gpio_num, true);
    
    // Interrupt setup for zero-crossing event in outage detection
    dev->driver_enable_gpio_global_interrupt();
    dev->driver_set_gpio_callback(dev->gpio_num, cb_zerocross);
}

bool app_is_outage_occured(app_outage_t *dev) {
    uint32_t tick_current;
    uint32_t diff;
    tick_current = driver_rp2_get_global_tick();
    // check overflow at 0xFFFF
    if (tick_current < tick_zerocross) {
        diff = (0xFFFF - tick_zerocross) + tick_current + 1; 
    }
    else {
        diff = tick_current - tick_zerocross;
    }

    return (diff >= dev->threshold);
}
