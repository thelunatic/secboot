/*
 * Copyright (c) 2021 Regents of the University of Colorado.
 * Developed by the Embedded Systems and Security lab <essl@uccs.edu>
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

int COMPLEX[4] = {0,0,0,0};
int SIMPLE[4] = {0,0,0,0};
rtems_id semaphore;
rtems_id c_tid[4];
rtems_id s_tid[4];

static void
safety_task(rtems_task_argument number){

    int val = 0;
    int temp1 = 0;
    int temp2 = 1;
    int i = 0;
    uint_fast32_t time_tick;
    rtems_status_code sc;

    while(1){
        i = i % 4;
        printk("\n SAFETY TASK %d STARTED", (int)number);
        time_tick = T_get_one_clock_tick_busy();
        T_busy(time_tick/4);
        SIMPLE[i] = 1;
        i++;
        sleep(0.25);
        printk("\n SAFETY TASK %d OVER\n", (int) number);
    }

    rtems_task_exit();
}

static void
complex_task(rtems_task_argument number){

    int val = 0;
    int temp1 = 0;
    int temp2 = 1;
    int i = 0;
    uint_fast32_t time_tick;
    rtems_status_code sc;

    while(1){
        i = i%4;
        printk("\n COMPLEX TASK %d STARTED", (int)number);
        time_tick = T_get_one_clock_tick_busy();
        T_busy(time_tick/8);
        COMPLEX[i] = 1;
        ++i;
        sleep(0.25);
        printk("\n COMPLEX TASK %d OVER\n", (int)number);
    }

    rtems_task_exit();
}

static void
safety_set(){
    rtems_id tid[4];
    char ch = '0';
    rtems_status_code sc;

    for(int i=0; i<3; ++i){
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

    for(int i=0; i<3; ++i){
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

#if 0
static void
microreboot_task(rtems_task_argument arg){
    printk("\n MICROREBOOT REACHED");
    for (int i = 1; i < 2; ++i){
        //sleep(1);
        //sched_yield();
        rtems_status_code sc = rtems_semaphore_obtain( semaphore, RTEMS_WAIT, 0);
        assert(sc == RTEMS_SUCCESSFUL);

        COMPLEX++;

        sc = rtems_semaphore_release(semaphore);
        assert(sc == RTEMS_SUCCESSFUL);

        rtems_task_restart((rtems_id) arg, 0);
    }

    rtems_task_exit();
}
#endif

static void
decision_module(rtems_task_argument arg){
    (void) arg;
    rtems_status_code sc;
    printk("\n DECISION MODULE STARTED");
#if 0
    sc = rtems_semaphore_obtain( semaphore, RTEMS_WAIT, 0);
    assert(sc == RTEMS_SUCCESSFUL);
#endif

    while(1){
        for (int i = 0; i < 4; ++i){
            if (SIMPLE[i] == COMPLEX[i]){
                printk("\n\n == DECISION: COMPLEX MODULE == ");

            }
            else{
                printk("\n\n == DECISION: SAFETY MODULE == ");
                rtems_task_restart(c_tid[i], i);
            }

        }
        sleep(2);

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
    uint32_t prio_list[] = {0, 1, 2, 2};

    printk("\n SYSTEM STARTED");

    //printk("\n ALL TASKS STARTED");

#if 0
    sc = rtems_semaphore_create(
         rtems_build_name ('S', 'E', 'M', '1'),
         1,
         RTEMS_BINARY_SEMAPHORE |
         RTEMS_GLOBAL |
         RTEMS_PRIORITY,
         1,
         &semaphore);
    assert(sc == RTEMS_SUCCESSFUL);
#endif

    safety_set();
    complex_set();
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

#define CONFIGURE_SCHEDULER_EDF
//#define CONFIGURE_SCHEDULER_PRIORITY
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
