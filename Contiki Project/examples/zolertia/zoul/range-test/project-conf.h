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
 * \addtogroup zoul-examples
 * @{
 *
 * \defgroup remote-range-test RE-Mote 2.4GHz/Sub-1Ghz RF range test
 *
 * Implements a range test with PRR, LQI/RSSI measurements, using a LCD to
 * display the results
 *
 * @{
 *
 * \file
 *  Configuration file for the range test application
 *
 * \author
 *         Antonio Lignan <alinan@zolertia.com>
 */
#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#undef NETSTACK_CONF_RADIO

#ifdef RF_SUBGHZ
#define NETSTACK_CONF_RADIO           cc1200_driver
#define CC1200_CONF_USE_GPIO2         0
#define CC1200_CONF_USE_RX_WATCHDOG   0
#define RF_STRING                     "cc1200 RF 868MHz"
#define ANTENNA_SW_SELECT_DEF_CONF    ANTENNA_SW_SELECT_SUBGHZ
#else  /* RF_SUBGH */
#define NETSTACK_CONF_RADIO           cc2538_rf_driver
#define RF_STRING                     "cc2538 RF 2.4GHz"
#define ANTENNA_SW_SELECT_DEF_CONF    ANTENNA_SW_SELECT_2_4GHZ
#endif /* RF_SUBGHZ */

#define NETSTACK_CONF_RDC           nullrdc_driver

#endif /* PROJECT_CONF_H_ */

/**
 * @}
 * @}
 */
