/*
 * Copyright (c) 2020 Vijay Kumar Banerjee <vijay@rtems.org>.
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

#define PRIO_SHELL      150
#define STACK_SIZE_SHELL    (64 * 1024)
#define PRIO_MOUSE          (RTEMS_MAXIMUM_PRIORITY - 10)

typedef struct evdev_message {
    int fd;
    char device[256];
} evdev_message;

static rtems_id eid, emid;
static volatile bool kill_evtask, evtask_active;

static void*
tick_thread (void *arg)
{
    (void)arg;
    while(1) {
    }
}

static void
evdev_input_task(rtems_task_argument arg)
{
    rtems_status_code sc;
    size_t size;
    int fd = -1;
    pthread_t thread_id;

    evdev_message msg;

    kill_evtask = false;
    evtask_active = true;


    pthread_create(&thread_id, NULL, tick_thread, NULL);
    evtask_active = false;
    rtems_task_delete(RTEMS_SELF);
}

void
libbsdhelper_start_shell(rtems_task_priority prio)
{
    rtems_status_code sc = rtems_shell_init(
        "SHLL",
        STACK_SIZE_SHELL,
        prio,
        CONSOLE_DEVICE_NAME,
        false,
        true,
        NULL
    );
    assert(sc == RTEMS_SUCCESSFUL);
}

static void sec_task(rtems_task_argument arg){
    printf("This is task %d\n", (int)arg);
}

static void
Init(rtems_task_argument arg)
{
    rtems_status_code sc;
    rtems_id tid[5];
    char ch = '0';
    int exit_code;
    (void)arg;

    for(int i=0; i<5; ++i){
        sc = rtems_task_create(
                rtems_build_name('T', 'A', '0', ch + i),
                100,
                RTEMS_MINIMUM_STACK_SIZE,
                RTEMS_DEFAULT_MODES,
                RTEMS_FLOATING_POINT,
                &tid[i]
                );
        sc = rtems_task_start(tid[0], sec_task, i);
        assert(sc == RTEMS_SUCCESSFUL);
    }

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
