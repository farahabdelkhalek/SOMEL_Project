/*
 * Copyright (c) 2015, Zolertia - http://www.zolertia.com
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */
/*---------------------------------------------------------------------------*/
/**
 * \addtogroup remote-range-test
 *
 * Implements a range test with PRR, LQI/RSSI measurements, using a LCD to
 * display the results
 *
 * @{
 *
 * \file
 *  Application file for the range test
 *
 * \author
 *         Antonio Lignan <alinan@zolertia.com>
 */
/*---------------------------------------------------------------------------*/
#include "contiki.h"
#include "cpu.h"
#include "sys/etimer.h"
#include "dev/leds.h"
#include "dev/watchdog.h"
#include "dev/serial-line.h"
#include "dev/sys-ctrl.h"
#include "net/netstack.h"
#include "dev/radio.h"
#include "dev/button-sensor.h"
#include "net/rime/broadcast.h"
#include "dev/rgb-bl-lcd.h"

#include <stdio.h>
#include <stdint.h>
/*---------------------------------------------------------------------------*/
#define LOOP_INTERVAL                  (CLOCK_SECOND * 2)
#define BROADCAST_CHANNEL              129
/*---------------------------------------------------------------------------*/
#define BUTTON_PRESS_COUNT_MODE        6
#define BUTTON_PRESS_COUNT_HALF        (BUTTON_PRESS_COUNT_MODE / 2)
#define BUTTON_PRESS_EVENT_INTERVAL    (CLOCK_SECOND)
/*---------------------------------------------------------------------------*/
static uint8_t colour;
static uint64_t prr;
#if LCD_ENABLED
  static char buf[17];
#endif
static uint16_t counter;
static uint16_t rx_packet;
static int8_t tx_mode, started;
/*---------------------------------------------------------------------------*/
static struct etimer et;
/*---------------------------------------------------------------------------*/
static void
broadcast_recv(struct broadcast_conn *c, const linkaddr_t *from)
{
  int8_t rssi;
  uint8_t lqi;
  uint16_t tx_expected;

 // if((tx_mode != 0) || (started < 0)){
  //  return;
  //}

  /* Increase the received packet counter */
  rx_packet++;

  lqi = packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY);
  rssi = (int8_t)packetbuf_attr(PACKETBUF_ATTR_RSSI);
  tx_expected = *(uint16_t *)packetbuf_dataptr();

  printf("*** Received %u bytes from %u:%u: '0x%04u' ", packetbuf_datalen(),
         from->u8[0], from->u8[1], tx_expected);
  printf("%04d - %02u\n", rssi, lqi);

  /* If receiving a packet with counter of zero, restart the statistics */
  if(tx_expected == 1) {
    prr = 0;
    rx_packet = 1;
  }

  /* Calculates Packet received ratio */
  prr = rx_packet * 1000;
  prr /= tx_expected;

  printf("*** PRR: %llu.%llu (rx %u exp %u)\n", prr / 10, prr % 10, rx_packet,
                                                tx_expected);

#if LCD_ENABLED
  lcd_set_cursor(0, LCD_RGB_1ST_ROW);
  snprintf(buf, 17, "RX %04u EXP %04u", rx_packet, tx_expected);
  lcd_write(buf);

  lcd_set_cursor(0, LCD_RGB_2ND_ROW);
  snprintf(buf, 17, "%04d dBm %02u %03u  ", rssi, lqi, (uint16_t)(prr / 10));
  lcd_write(buf);
#endif

  leds_toggle(colour);
}
/*---------------------------------------------------------------------------*/
static void
print_radio_info(void)
{
  radio_value_t ch, ch_min, ch_max, txp;

  printf("\nRadio information:\n");
  printf("  * %s\n", RF_STRING);

  if(NETSTACK_RADIO.get_value(RADIO_PARAM_CHANNEL, &ch) == RADIO_RESULT_OK) {
    printf("  * Channel %d ", ch);
  }

  if(NETSTACK_RADIO.get_value(RADIO_CONST_CHANNEL_MIN, &ch_min) ==
    RADIO_RESULT_OK) {
    printf("(%d-", ch_min);
  }

  if(NETSTACK_RADIO.get_value(RADIO_CONST_CHANNEL_MAX, &ch_max) ==
    RADIO_RESULT_OK) {
    printf("%d)\n", ch_max);
  }

  if(NETSTACK_RADIO.get_value(RADIO_PARAM_TXPOWER, &txp) == RADIO_RESULT_OK) {
    printf("  * TX power %d dBm [0x%04x]\n", txp, (uint16_t)txp);
  }

#if LCD_ENABLED
  lcd_set_cursor(0, LCD_RGB_2ND_ROW);
  snprintf(buf, 17, "Ch%02u %02u-%02u %02ddBm", ch, ch_min, ch_max, txp);
  lcd_write(buf);
#endif
}
/*---------------------------------------------------------------------------*/
static char *
mode_check(void)
{
  if(tx_mode) {
    return "TX";
  }
  return "RX";
}
/*---------------------------------------------------------------------------*/
static const struct broadcast_callbacks bc_rx = { broadcast_recv };
static struct broadcast_conn bc;
/*---------------------------------------------------------------------------*/
PROCESS(range_test_process, "Range test process");
AUTOSTART_PROCESSES(&range_test_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(range_test_process, ev, data)
{
  PROCESS_EXITHANDLER(broadcast_close(&bc))
  PROCESS_BEGIN();

  static uint8_t ticks;

  /* Configure the user button */
  button_sensor.configure(BUTTON_SENSOR_CONFIG_TYPE_INTERVAL,
                          BUTTON_PRESS_EVENT_INTERVAL);

#if LCD_ENABLED
  /* Enable the LCD */
  SENSORS_ACTIVATE(rgb_bl_lcd);

  lcd_backlight_color(LCD_RGB_WHITE);
  lcd_set_cursor(0, LCD_RGB_1ST_ROW);
  lcd_write("Range Test app");
#endif

  /* Print radio information */
  print_radio_info();

  etimer_set(&et, (CLOCK_SECOND * 5));
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&et));

  /* Configure the radio and network */
  broadcast_open(&bc, BROADCAST_CHANNEL, &bc_rx);

  /* Blink steady blue until the user long-press the user button to select the
   * operation mode, then it will blink red if in receiver mode, green if
   * transmission mode, until the user button is pressed again to start the test
   */

  ticks = 0;
  tx_mode = -1;
  started = -1;
  colour = LEDS_BLUE;

#if LCD_ENABLED
  lcd_set_cursor(0, LCD_RGB_1ST_ROW);
  lcd_write("Press and hold ");
  lcd_set_cursor(0, LCD_RGB_2ND_ROW);
  lcd_write("TX green, RX Red");
#endif

  leds_off(LEDS_ALL);
  etimer_set(&et, LOOP_INTERVAL);

  while(1) {
    PROCESS_YIELD();
    leds_toggle(colour);

#if LCD_ENABLED
    if(tx_mode >= 0) {
      lcd_set_cursor(0, LCD_RGB_2ND_ROW);
      lcd_write("Press to begin! ");
    }
#endif

    /* A single push event will start the test */
    if((ev == sensors_event) && (data == &button_sensor)) {
      if((button_sensor.value(BUTTON_SENSOR_VALUE_TYPE_LEVEL) ==
        BUTTON_SENSOR_PRESSED_LEVEL) && (tx_mode >= 0)) {
        printf("%s mode, press the user button to start!\n", mode_check());
        started = 1;
        break;
      }

    /* A long push will choose which operation mode to use */
    } else if(ev == button_press_duration_exceeded) {
      ticks++;

      if(ticks <= BUTTON_PRESS_COUNT_HALF) {
        tx_mode = 0;
        colour = LEDS_RED;
        leds_off(LEDS_BLUE + LEDS_GREEN);
        leds_on(colour);
#if LCD_ENABLED
        lcd_set_cursor(0, LCD_RGB_1ST_ROW);
        lcd_write("RX mode selected");
        lcd_backlight_color(LCD_RGB_RED);
#endif

      } else if(ticks <= BUTTON_PRESS_COUNT_MODE) {
        tx_mode = 1;
        colour = LEDS_GREEN;
        leds_off(LEDS_BLUE + LEDS_RED);
        leds_on(colour);
#if LCD_ENABLED
        lcd_set_cursor(0, LCD_RGB_1ST_ROW);
        lcd_write("TX mode selected");
        lcd_backlight_color(LCD_RGB_GREEN);
#endif

      } else {
        ticks = 0;
      }
    }
    etimer_restart(&et);
  }

  /* Start the test */
  printf("Test started!\n");
  etimer_set(&et, LOOP_INTERVAL);

#if LCD_ENABLED
  if(!tx_mode) {
    lcd_set_cursor(0, LCD_RGB_2ND_ROW);
    lcd_write("Waiting for data");
  }
#endif

  while(1) {
    PROCESS_YIELD();
    if(ev == PROCESS_EVENT_TIMER) {

      /* This works as expected received packets for the receiver, and the
       * transmitted packet for the sender node
       */
      counter++;

      if(tx_mode) {
        printf("Transmit (tx counter) %u\n", counter);
#if LCD_ENABLED
        lcd_set_cursor(0, LCD_RGB_2ND_ROW);
        snprintf(buf, 16, "packet --> %04u", counter);
        lcd_write(buf);
#endif
        leds_toggle(colour);
        packetbuf_copyfrom(&counter, sizeof(counter));
        broadcast_send(&bc);
        etimer_reset(&et);
      }
    }
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
/**
 * @}
 */

