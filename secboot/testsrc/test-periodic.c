/*
 * Copyright (c) 2022 Anonymous.
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
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>

#include <rtems.h>
#include <rtems/console.h>
#include <rtems/shell.h>
#include <rtems/btimer.h>
#include <rtems/test.h>
#include <rtems/bspIo.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <sys/time.h>

#include "sample-data.h"

#ifdef RAND_MAX
#undef RAND_MAX
#endif

#define RAND_MAX            100
#define PRIO_SHELL          150
#define STACK_SIZE_SHELL    (64 * 1024)
#define PRIO_MOUSE          (RTEMS_MAXIMUM_PRIORITY - 10)

#define TASK_EXEC_COUNT_MAX 10
#define JOB_MAX 5
#define SFTY_IDX 0
#define CMPLX_IDX 1
#define HYPER_PERIOD 15
#define SPRIO 10
#define CPRIO 10

int COMPLEX[4][50] = {{}};
int SIMPLE[4][50] = {{}};
rtems_id COMPLEX_PERIOD[4] = {};
int complex_counter[4] = {};
rtems_id semaphore;
rtems_id c_tid[4];
rtems_id s_tid[4];


static void
safety_task(rtems_task_argument number){

    rtems_name name;
    rtems_id period;
    rtems_status_code sc;
    rtems_interval ticks;

    int val = 0;
    int temp1 = 0;
    int temp2 = 1;
    int temp3 = 0;
    int i = 0;
    struct timeval tv;
    uint_fast32_t time_tick;

    name = rtems_build_name( 'S', 'A', 'F', (char)'0' + number );

    sc = rtems_rate_monotonic_create( name, &period);
    assert(sc == RTEMS_SUCCESSFUL);

    while(1){
        //printk("\n SAFETY TASK %d STARTED", (int)number);
        gettimeofday(&tv,0);
        if (rtems_rate_monotonic_period(period, 568) == RTEMS_TIMEOUT){
            printk("\n SAFETY TASK MISSED DEADLINE");
    //        break;
        }
#if 0
        i = i % 50;
        temp3 = temp1 + data[i];
#endif
        ticks = rtems_clock_get_ticks_per_second();
        time_tick = ticks*T_get_one_clock_tick_busy()/1000;
        printk("\n time now for SFT%d=  %lld", number, tv.tv_sec*1000000 + tv.tv_usec);
        T_busy(100*time_tick);
#if 0
        SIMPLE[number][i] = temp3;
        i++;
        //printk("\n SAFETY TASK %d OVER\n", (int) number);
#endif
    }

#if 0
    sc = rtems_rate_monotonic_delete(period);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_delete(rtems_task_self());
    assert(sc == RTEMS_SUCCESSFUL);
#endif
    rtems_task_exit();

}

static void
complex_task(rtems_task_argument number){

    rtems_name name;
    rtems_id period;
    rtems_status_code sc;
    rtems_interval ticks;

    int val = 0;
    int temp1 = 0;
    int temp2 = 1;
    int temp3 = 0;
    int i = 0;
    uint_fast32_t time_tick;
    struct timeval tv;

    name = rtems_build_name( 'C', 'P', 'X', (char)'0' + number );

    sc = rtems_rate_monotonic_create( name, &period);
    assert(sc == RTEMS_SUCCESSFUL);

    COMPLEX_PERIOD[number] = period;

    while(1){
        gettimeofday(&tv,0);
        if (rtems_rate_monotonic_period(period, 500) == RTEMS_TIMEOUT){
            printk("\n COMPLEX TASK MISSED DEADLINE");
       //     break;
        }
#if 0
        i = complex_counter[number];
        i = i%50;
        temp3 = temp1 + data[i];
#endif
        ticks = rtems_clock_get_ticks_per_second();
        time_tick = ticks*T_get_one_clock_tick_busy()/1000;
        printk("\n time now for CMP%d=  %lld", number, tv.tv_sec*1000000 + tv.tv_usec);
        T_busy(50*time_tick);
#if 0
        COMPLEX[number][i] = temp3;
        
        complex_counter[number] = i + 1;
#endif
    }
#if 1
    sc = rtems_rate_monotonic_delete(period);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_delete(rtems_task_self());
    assert(sc == RTEMS_SUCCESSFUL);
#endif


    rtems_task_exit();
}

static rtems_status_code
task_restart(int task_num){
    rtems_task_delete(c_tid[task_num]);
    rtems_rate_monotonic_delete(COMPLEX_PERIOD[task_num]);
    rtems_status_code sc;

    sc = rtems_task_create(
          rtems_build_name('C', 'M', 'P', (char)'0' + task_num),
          CPRIO,
          RTEMS_MINIMUM_STACK_SIZE,
          RTEMS_DEFAULT_MODES,
          RTEMS_FLOATING_POINT,
          &c_tid[task_num]
         );
    assert(sc == RTEMS_SUCCESSFUL);
    sc = rtems_task_start(c_tid[task_num], complex_task, task_num);

    return sc;
}

static void
safety_set(){
    rtems_id tid[4];
    char ch = '0';
    rtems_status_code sc;

    for(int i=0; i<4; ++i){
        sc = rtems_task_create(
              rtems_build_name('S', 'F', 'T', ch + i),
              SPRIO,
              RTEMS_MINIMUM_STACK_SIZE,
              RTEMS_DEFAULT_MODES,
              RTEMS_FLOATING_POINT,
              &s_tid[i]
             );
        assert(sc == RTEMS_SUCCESSFUL);
        sc = rtems_task_start(s_tid[i], safety_task, i);
        assert(sc == RTEMS_SUCCESSFUL);
    }

}

static void
complex_set(){
    rtems_id tid[4];
    char ch = '0';
    rtems_status_code sc;

    for(int i=0; i<4; ++i){
        sc = rtems_task_create(
              rtems_build_name('C', 'M', 'P', ch + i),
              CPRIO,
              RTEMS_MINIMUM_STACK_SIZE,
              RTEMS_DEFAULT_MODES,
              RTEMS_FLOATING_POINT,
              &c_tid[i]
             );
        assert(sc == RTEMS_SUCCESSFUL);
        sc = rtems_task_start(c_tid[i], complex_task, i);
        assert(sc == RTEMS_SUCCESSFUL);
    }

}

static void
microreboot_task(){
    rtems_name name;
    rtems_id period;
    rtems_status_code sc;
    int reset_counter = 0;
    printk("\n MICROREBOOT MODULE STARTED");

    name = rtems_build_name( 'M', 'I', 'C', 'R' );

    sc = rtems_rate_monotonic_create( name, &period);
    assert(sc == RTEMS_SUCCESSFUL);

    while(1){
        if (rtems_rate_monotonic_period(period, 10000) == RTEMS_TIMEOUT){
            break;
        }
        //sleep(16);
        reset_counter %= 4;
        sc = task_restart(reset_counter++);
        if (sc != RTEMS_SUCCESSFUL){
            printk("\n MICROREBOOT FAILED FOR: TASK %d TID: %d",
                   reset_counter-1, c_tid[reset_counter-1]);
        }
        else{
            printk("\n MICROREBOOTED TASK %d TID: %d",
                   reset_counter-1, c_tid[reset_counter-1]);

        }

        reset_counter %= 4;
        sc = task_restart(reset_counter++);
        if (sc != RTEMS_SUCCESSFUL){
            printk("\n MICROREBOOT FAILED FOR: TASK %d TID: %d",
                   reset_counter-1, c_tid[reset_counter-1]);
        }
        else{
            printk("\n MICROREBOOTED TASK %d TID: %d",
                   reset_counter-1, c_tid[reset_counter-1]);

        }

    }
#if 0
    sc = rtems_rate_monotonic_delete(period);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_delete(rtems_task_self());
    assert(sc == RTEMS_SUCCESSFUL);
#endif

    rtems_task_exit();
}

static void
microreboot_module(){
    rtems_id mid;
    rtems_status_code sc;
    printk("\n SECURE MICROREBOOT MODULE STARTED");
#if 0
    sc = rtems_semaphore_obtain( semaphore, RTEMS_WAIT, 0);
    assert(sc == RTEMS_SUCCESSFUL);
#endif
    sc = rtems_task_create(
          rtems_build_name('M', 'R', 'B', 'T' ),
          10,
          RTEMS_MINIMUM_STACK_SIZE,
          RTEMS_DEFAULT_MODES,
          RTEMS_FLOATING_POINT,
          &mid
         );
    assert(sc == RTEMS_SUCCESSFUL);
    sc = rtems_task_start(mid, microreboot_task, 0);
    assert(sc == RTEMS_SUCCESSFUL);
}

static void
decision_module(rtems_task_argument arg){
    (void) arg;

    rtems_name name;
    rtems_id period;
    rtems_status_code sc;
    int counter = 0;
    printk("\n DECISION MODULE STARTED");

    //printk("\n SET      SAFETY        COMPLEX     DECISION ");

    while(1){
#if 0
        for (int i = 0; i < 4; ++i){
            //for (int j = 0; j < 4; j++){
                counter %= 50;
                if (SIMPLE[i][counter] == COMPLEX[i][counter]){
                    //printk("\n %d          %d               %d       COMPLEX", i, SIMPLE[i][counter], COMPLEX[i][counter]);
                    //printk("\n\n == DECISION FOR SET #%d: COMPLEX MODULE == ", i);

                }
                else{
     //               printk("\n %d          %d               %d       SAFETY <===", i, SIMPLE[i][counter], COMPLEX[i][counter]);
                    //task_restart(i);
                }
            }
                counter++;
        //}
#endif
        printk("\n");
        rtems_rate_monotonic_report_statistics();
        sleep(3);

    }

#if 0
    sc = rtems_semaphore_release(semaphore);
    assert(sc == RTEMS_SUCCESSFUL);
#endif

    rtems_task_exit();
}

static void
Init(rtems_task_argument arg){
    rtems_status_code sc;
    rtems_id tid[5];
    char ch = '0';
    (void)arg;

    printk("\n SYSTEM STARTED");

    //printk("\n ALL TASKS STARTED");

    safety_set();
    complex_set();
    //microreboot_module();
    decision_module(0);

    sleep(HYPER_PERIOD);
    exit(0);
}
/*
 * Configure RTEMS.
 */
#define CONFIGURE_MICROSECONDS_PER_TICK 1000

#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_CONSOLE_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_STUB_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_ZERO_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_LIBBLOCK

#define CONFIGURE_FILESYSTEM_DOSFS
#define CONFIGURE_MAXIMUM_FILE_DESCRIPTORS 32

#define CONFIGURE_UNLIMITED_OBJECTS
#define CONFIGURE_UNIFIED_WORK_AREAS
#define CONFIGURE_MAXIMUM_USER_EXTENSIONS 1

//#define CONFIGURE_SCHEDULER_EDF
#define CONFIGURE_SCHEDULER_PRIORITY
#define CONFIGURE_INIT_TASK_STACK_SIZE (64*1024)
#define CONFIGURE_INIT_TASK_INITIAL_MODES RTEMS_DEFAULT_MODES
#define CONFIGURE_INIT_TASK_ATTRIBUTES RTEMS_FLOATING_POINT

#define CONFIGURE_BDBUF_BUFFER_MAX_SIZE (32 * 1024)
#define CONFIGURE_BDBUF_MAX_READ_AHEAD_BLOCKS 4
#define CONFIGURE_BDBUF_CACHE_MEMORY_SIZE (1 * 1024 * 1024)
#define CONFIGURE_BDBUF_READ_AHEAD_TASK_PRIORITY 97
#define CONFIGURE_SWAPOUT_TASK_PRIORITY 97

#define CONFIGURE_RTEMS_INIT_TASKS_TABLE
#define CONFIGURE_INIT

#include <bsp/irq-info.h>
#include <bsp/i2c.h>
#include <rtems/confdefs.h>

#include <rtems/shellconfig.h>
