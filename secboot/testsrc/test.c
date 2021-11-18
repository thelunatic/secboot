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

#include <rtems.h>
#include <rtems/console.h>
#include <rtems/shell.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>

#ifdef RAND_MAX
#undef RAND_MAX
#endif

#define RAND_MAX            100
#define PRIO_SHELL          150
#define STACK_SIZE_SHELL    (64 * 1024)
#define PRIO_MOUSE          (RTEMS_MAXIMUM_PRIORITY - 10)

static rtems_id eid, emid;
static volatile bool kill_evtask, evtask_active;

struct tsk_arg{
  int num;
  rtems_id tid;
};

static void*
tick_thread (void *arg)
{
    (void)arg;
    while(1) {
    }
}

static int safety_task(){
    return 0;
}

static void
restart_task(){
    sleep(3);
    exit(0);
}

static void
microreboot_task(rtems_task_argument arg){
    rtems_id id = (rtems_id) arg;
    printf("Restarting task with task id: %d\n", id);
    rtems_task_restart(id, 0);
}

static void
complex_task(rtems_task_argument arg){

    int val = 0;
    int temp1 = 0;
    int temp2 = 1;
    for (int i = 0; i < 1000000; ++i){
        val = temp1 + temp2;
        temp1 = temp2;
        temp2 = val;
    }
}

static void sec_task(rtems_task_argument arg){
    struct tsk_arg ta;// = arg;
    int num = ta.num;
    rtems_id tid = ta.tid;
    
    if (num == 2){  //SC Task
        /*
          check the value of global var TEMP,
          return temp+2.
          Value is always withing 100 +- 10
        */
    }
    if (num == 3){  // CC Task
        /*
          same as sc task, but without range check
        */
    }
    if (num == 4){  //DM Task
        /*
           Check the output from the CC task and decide whether
           to output SC or CC output.
        */
    }
        if (num == 5){  // CC Task
        /*
          same as cc task, but without a parallel sc task (this internal CC task is used to experiment what happens to the other existing taks in the system which have nothing to do with the controller output)
        */
        }
    printf("This is task %d\n", (int)arg);
}

static void
Init(rtems_task_argument arg){
    rtems_status_code sc;
    rtems_id tid[5];
    char ch = '0';
    int exit_code;
    (void)arg;

    for(int i=0; i<6; ++i){
        sc = rtems_task_create(
                rtems_build_name('T', 'A', '0', ch + i),
                100,
                RTEMS_MINIMUM_STACK_SIZE,
                RTEMS_DEFAULT_MODES,
                RTEMS_FLOATING_POINT,
                &tid[i]
                );
    }
    sc = rtems_task_start(tid[0], restart_task, 0);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_start(tid[1], microreboot_task, tid[2]);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_start(tid[2], complex_task, 0);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_start(tid[0], sec_task, 0);
    assert(sc == RTEMS_SUCCESSFUL);

    sc = rtems_task_start(tid[0], sec_task, 0);
    assert(sc == RTEMS_SUCCESSFUL);

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

#define CONFIGURE_INIT_TASK_STACK_SIZE (64*1024)
#define CONFIGURE_INIT_TASK_INITIAL_MODES RTEMS_DEFAULT_MODES
#define CONFIGURE_INIT_TASK_ATTRIBUTES RTEMS_FLOATING_POINT

#define CONFIGURE_BDBUF_BUFFER_MAX_SIZE (32 * 1024)
#define CONFIGURE_BDBUF_MAX_READ_AHEAD_BLOCKS 4
#define CONFIGURE_BDBUF_CACHE_MEMORY_SIZE (1 * 1024 * 1024)
#define CONFIGURE_BDBUF_READ_AHEAD_TASK_PRIORITY 97
#define CONFIGURE_SWAPOUT_TASK_PRIORITY 97

//#define CONFIGURE_STACK_CHECKER_ENABLED

#define CONFIGURE_RTEMS_INIT_TASKS_TABLE
#define CONFIGURE_INIT

#include <bsp/irq-info.h>
#include <bsp/i2c.h>
#include <rtems/confdefs.h>

#include <rtems/shellconfig.h>
