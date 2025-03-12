#include "board_driver_rp2.h"



// array of GPIO callback functions
static void (*gpio_cb[TOTAL_NUM_GPIO_RP2]) ();

// static vars for Timer
static struct repeating_timer t;
static uint32_t global_tick=0;

// ISR for GPIO
static void isr_gpio(uint gpio, uint32_t events) {
    gpio_cb[gpio]();
}

static bool isr_global_timer(struct repeating_timer *t) {
    global_tick++;
}

void driver_rp2_sysinit() {
    // Use printf as serial print on USB
    stdio_init_all();

    // setup clock speed
    clock_configure(clk_ref,
                    0,
                    0,
                    12 * MHZ,
                    12 * MHZ);
}

void driver_rp2_set_gpio_input(uint8_t gpio_num, bool use_interrupt) {
    // Direction and pull-up setup
    gpio_set_function((unsigned char)gpio_num, GPIO_FUNC_SIO);
    gpio_set_dir(gpio_num, GPIO_IN);
    gpio_pull_up(gpio_num);
    
    // Enable an interrupt for target pin
    if (use_interrupt) {
        gpio_set_irq_enabled ((unsigned char)gpio_num, GPIO_IRQ_EDGE_FALL, true);
    }
}

void driver_rp2_enable_gpio_global_interrupt() {
    irq_set_enabled(IO_IRQ_BANK0, true);
    gpio_set_irq_callback (isr_gpio);
}

void driver_rp2_set_gpio_callback(uint8_t gpio_num, void (*cb) (void)) {
    gpio_cb[gpio_num] = cb;
}

bool driver_rp2_read_gpio(uint8_t gpio_num) {
    bool value;
    value = gpio_get(gpio_num);
    return value;
}

void driver_rp2_set_gpio_output(uint8_t gpio_num) {
    // Direction and pull-up setup
    gpio_set_function((unsigned char)gpio_num, GPIO_FUNC_SIO);
    gpio_set_dir((unsigned char)gpio_num, GPIO_OUT);
    gpio_disable_pulls((unsigned char)gpio_num);
}

void driver_rp2_write_gpio(uint8_t gpio_num, bool value) {
    gpio_put((unsigned char)gpio_num, value);
}

void driver_rp2_create_global_tick(uint32_t tick_period_ms) {
    add_repeating_timer_ms(tick_period_ms, isr_global_timer, NULL, &t);
}

uint32_t driver_rp2_get_global_tick() {
    return global_tick;
}
