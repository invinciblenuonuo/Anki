# RTOS

## 内核态，用户态的区别

区别：运行级别，是否可以操作硬件

用户态->内核态：系统调用、异常、外围设备中断



## 进程、线程



概述区别

1. 地址

- 进程是资源分配的最小单位，线程是CPU调度的最小单位，进程有独立分配的内存空间，线程共享进程空间
- 真正在cpu上运行的是线程

2. 开销

- 进程切换开销大，线程轻量级

3. 并发性

- 进程并发性差

4. 崩溃

- 线程的崩溃不一定导致进程的崩溃




- 线程在进程下行进（单纯的车厢无法运行）
- 一个进程可以包含多个线程（一辆火车可以有多个车厢）
- 不同进程间数据很难共享（一辆火车上的乘客很难换到另外一辆火车，比如站点换乘）
- 同一进程下不同线程间数据很易共享（A车厢换到B车厢很容易）
- 进程要比线程消耗更多的计算机资源（采用多列火车相比多个车厢更耗资源）
- 进程间不会相互影响，一个线程挂掉将导致整个进程挂掉（一列火车不会影响另外一列火车，但如果一列火车上中间的一节车厢着火了，将影响到所有车厢）
- 进程可以拓展到多机，进程最多适合多核（不同火车可以开在多个轨道上，同一火车的车厢不能在行进的不同的轨道上）
- 进程使用的内存地址可以上锁，即一个线程使用某些共享内存时，其他线程必须等它结束，才能使用这一块内存。（比如洗手间）－"互斥锁"
- 进程使用的内存地址可以限定使用量（比如火车上的餐厅，最多只允许多少人进入，如果满了需要在门口等，等有人出来了才能进去）－“信号量”



1. 资源占用：每个进程都有独立的内存空间，包括代码、数据、堆栈等，而线程共享所属进程的内存空间。因此，在创建、切换和销毁进程时，涉及到较大的资源开销，而线程切换和创建时的开销较小。
2. 并发性：进程是独立运行的执行单位，多个进程之间可以并发，每个进程都有自己的执行状态、程序计数器和堆栈指针等。线程是进程内的执行流，多个线程共享进程的资源，在同一进程中的个线程可以并发执行。
3. 通信和同步：进程间的通信比较复杂，需要通过特定的机制（如管道、消息队列、等）进行数据的传递和共享。而线程之间共享进程的资源，通信相对容易，可以直接访问共享的内存变量。在多线程编程中，线程之间需要通过同步机制（如锁、信号量、条件变量等）来保证数据的一致性和正确性。
4. 安性：由于线程共享进程的资源，多个线程之间对共享数据的访问需要进行同步控制，否则可能会出现竞争条件（Race Condition）和数据不一致的问题。相比之下，进程间的数据相对独立，每个进程拥有独立的内存空间，更加安全。



## 什么时候使用进程与线程

多进程：

- 优点：进程独立，不影响主程序稳定性，可多CPU运行
- 缺点：逻辑复杂，IPC通信困难，调度开销大

多线程：

- 优点：线程间通信方便，资源开销小，程序逻辑简单
- 缺点：线程间独立互斥困难，线程崩溃影响进程

选择：频繁创建的用线程，CPU密集用进程，IO密集用线程

**总结：安全稳定选进程，快速频繁选线程**



## 为什么进程切换比线程切换慢

所需保存的上下文不同

- 进程切换涉及到页表的切换，页表的切换实质上导致TLB的缓存全部失效，这些寄存器里的内容需要全部重写。而线程切换无需经历此步骤。
- 线程切换涉及到线程栈



## 进程可以创建线程数量

（可用虚拟空间和线程的栈的大小共同决定）一个进程可用虚拟空间是2G，默认情况下，线程的栈的大小是1MB，所以理论上最多只能创建2048个线程



## TCB与PCB

线程控制块与进程控制块

PCB：

- 进程ID
- 进程状态寄存器
- 锁、信号量等同步机制与上下文信息
- 进程优先级、等待时间等其他内存
- 内存空间范围
- 线程状态
- 文件描述符

TCB：

- 线程ID
- 线程状态寄存器
- 锁、信号量等同步机制与上下文信息
- 线程优先级



## 进程上下文切换保存的数据

PCB、CPU通用寄存器、浮点寄存器、用户栈、内核数据结构（页表、进程表、文件表）



## 线程上下文切换保存的内容

- TCB信息
- 寄存器状态：如R0-R3、SP、LR、PC等
- 程序状态字：如程序处于中断、用户态、内核态等标志位
- 堆栈：线程执行期间所用的变量等信息
- 浮点FPU寄存器

![5b0d565b5e8841d6b76d514ebbf643f6.jpeg](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/5b0d565b5e8841d6b76d514ebbf643f6.jpeg)



## TLB（Translation Lookaside Buffer）

页表的cache，也称为快表，属于MMU的一部分



## TLB、页表、Cache、主存之间的访问关系

首先，程序员应该给出一个逻辑地址。通过逻辑地址去查询TLB和页表（一般是同时查询，TLB是页表的子集，所以TLB命中，页表一定命中；但是页表命中，TLB不一定命中），以确定该数据是否在主存中。因为只要TLB和页表命中，该数据就一定被调入主存。如果TLB和页表都不命中，则代表该数据就不在主存，所以必定会导致Cache访问不命中。现在，假设该数据在主存中，那么Cache也不一定会命中，因为Cache里面的数据仅仅是主存的一小部分。







## 任务调度

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MzkxNDYwNA==,size_16,color_FFFFFF,t_70.png" alt="在这里插入图片描述" style="zoom: 67%;" />



## 父子进程、僵尸、孤儿

子进程：父进程执行fork()系统调用，复制出一个和自身基本一致的进程为子进程，随后执行exec()系统调用，父进程执行其他任务

孤儿进程： 父进程生成子进程，但是父进程比子进程先结束，系统在子进程结束后回收资源

僵尸进程：子进程已经退出，但是没有父进程回收它的资源

fork()：建立一个新的子进程。其子进程会复制父进程的数据与堆栈空间，并继承已打开的文件代码、工作目录和资源限制等



## 死锁的原因、条件

两个或两个以上的进程在，因争夺资源而造成的一种互相等待的现象

原因：资源不足、分配不当、推进顺序不合适

条件：

​		（1） **互斥条件**：一个资源每次只能被一个进程使用。
​		（2） **不剥夺条件**：进程已获得的资源，在末释放前，不能强行剥夺。
​		（3） **请求与保持条件**：一个进程因请求资源而阻塞时，对已获得的资源保持不放。
​		（4） **循环等待条件**：若干进程之间形成一种头尾相接的循环等待资源关系。

解除与预防：打破上述一个条件即可



## OS中原子操作是如何实现的

底层通过关闭中断或原子指令（硬件支持）的方式

Linux通过原子指令



## 进程间通信

**进程有独立的地址空间，线程公用地址空间。**

| 类别 | 信号   | 信号量           | 消息队列 | 管道                                            | 共享内存                                 | socket         |
| ---- | ------ | ---------------- | -------- | ----------------------------------------------- | ---------------------------------------- | -------------- |
| 描述 | 软中断 | 计数器，同步互斥 | 消息链表 | 无名管道（父子进程间通信）+有名管道（FIFO文件） | 将同一块内存映射到不同进程（最快最有效） | 面向网络的通信 |
| 流向 |        |                  | 单向     | 单向                                            | 双向                                     |                |

事件不是进程间通信的方式

## 有名管道、无名管道

进程间通信（IPC）是指操作系统中不同进程之间进行数据交换和共享的机制。无名管道和有名管道都是常见的进程间通信方式。

1. 无名管道（Unnamed Pipe）：
    - 无名管道是一种半双工的、只能在具有公共祖先的进程之间使用的通信机制。
    - 创建无名管道时，操作系统会为其分配一个读端和一个写端。
    - 数据通过管道在进程之间单向流动，一端写入数据，另一端从中读取。
    - 无名管道通常用于父子进程之间的通信，可以通过fork()系统调用创建。
    - 无名管道只能用于有亲缘关系的进程之间的通信，无法被其他进程访问。
2. 有名管道（Named Pipe）：
    - 有名管道也称为FIFO（First In, First Out），它提供了一种在无亲缘关系的进程之间进行通信的方法。
    - 有名管道通过在文件系统中创建一个特殊类型的文件来实现，该文件具有独立的文件名。
    - 不同进程可以通过打开该文件并对其进行读写来进行通信。
    - 有名管道允许多个进程同时向其中写入数据或者从中读取数据。
    - 有名管道可以被许多不相关的进程使用，提供了一种灵活的进程间通信方式。

无名管道和有名管道都是通过读写文件描述符来进行通信的。它们在实现上有所差异，适用于不同的场景和需求。



## 线程间通信

**进程有独立的地址空间，线程公用地址空间。**

信号、互斥锁、读写锁、自旋锁、条件变量、信号量

线程间无需特别的手段进行通信，因为线程间可以共享一份全局内存区域，其中包括初始化数据段、未初始化数据段，以及堆内存段等，所以线程之间可以方便、快速地共享信息。只需要将数据复制到共享（全局或堆）变量中即可。不过，要考虑线程的同步和互斥，应用到的技术有： 

- 信号 Linux 中使用 pthread_kill() 函数对线程发信号。 
- 互斥锁确保同一时间只能有一个线程访问共享资源，当锁被占用时试图对其加锁的线程都进入阻塞状态（释放 CPU 资源使其由运行状态进入等待状态），当锁释放时哪个等待线程能获得该锁取决于内核的调度。
- 读写锁当以写模式加锁而处于写状态时任何试图加锁的线程（不论是读或写）都阻塞，当以读状态模式加锁而处于读状态时“读”线程不阻塞，“写”线程阻塞。读模式共享，写模式互斥。
- 自旋锁上锁受阻时线程不阻塞而是在循环中轮询查看能否获得该锁，没有线程的切换因而没有切换开销，不过对 CPU 的霸占会导致 CPU 资源的浪费。 所以自旋锁适用于并行结构（多个处理器）或者适用于锁被持有时间短而不希望在线程切换产生开销的情况。 
- 条件变量 条件变量可以以原子的方式阻塞进程，直到某个特定条件为真为止。对条件的测试是在互斥锁的保护下进行的，条件变量始终与互斥锁一起使用。
- 信号量 信号量实际上是一个非负的整数计数器，用来实现对公共资源的控制。在公共资源增加的时候，信号量就增加；公共资源减少的时候，信号量就减少；只有当信号量的值大于0的时候，才能访问信号量所代表的公共资源。



## 条件变量condition variable

c++11中，当条件不满足时，相关线程被一直阻塞，直到某种条件出现，这些线程才会被唤醒

- 线程的阻塞是通过成员函数wait()/wait_for()和wait_until()实现
- 线程唤醒是通过函数notify_all()和notify_one()实现

虚假唤醒：在正常情况下，wait类型函数返回时要么是因为被唤醒，要么是因为超时才返回，但是在实际中发现，因此操作系统的原因，wait类型在不满足条件时，它也会返回，这就导致了虚假唤醒。

```c++
if (不满足xxx条件) {
    //没有虚假唤醒，wait函数可以一直等待，直到被唤醒或者超时，没有问题。
    //但实际中却存在虚假唤醒，导致假设不成立，wait不会继续等待，跳出if语句，
    //提前执行其他代码，流程异常
    wait();  
}
 
//其他代码
...

// 实际使用：
    
while (!(xxx条件) )
{
    //虚假唤醒发生，由于while循环，再次检查条件是否满足，
    //否则继续等待，解决虚假唤醒
    wait();  
}
//其他代码
....
```



案例：生产者消费者模式

```c++
#include <mutex>
#include <deque>
#include <iostream>
#include <thread>
#include <condition_variable>
 
class PCModle {
 public:
  PCModle() : work_(true), max_num(30), next_index(0) {
  }
 
  void producer_thread() {
    while (work_) {
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
 
      //加锁
      std::unique_lock<std::mutex> lk(cvMutex);
      //当队列未满时，继续添加数据
      cv.wait(lk, [this]() { return this->data_deque.size() <= this->max_num; });
 
      next_index++;
      data_deque.push_back(next_index);
      std::cout << "producer " << next_index << ", queue size: " << data_deque.size() << std::endl;
      //唤醒其他线程
      cv.notify_all();
      //自动释放锁
    }
  }
 
  void consumer_thread() {
    while (work_) {
      //加锁
      std::unique_lock<std::mutex> lk(cvMutex);
      //检测条件是否达成
      cv.wait(lk, [this] { return !this->data_deque.empty(); });
 
      //互斥操作，消息数据
      int data = data_deque.front();
      data_deque.pop_front();
      std::cout << "consumer " << data << ", deque size: " << data_deque.size() << std::endl;
      //唤醒其他线程
      cv.notify_all();
      //自动释放锁
    }
  }
  
 private:
  bool work_;
 
  std::mutex cvMutex;
  std::condition_variable cv;
 
  //缓存区
  std::deque<int> data_deque;
  //缓存区最大数目
  size_t max_num;
  //数据
  int next_index;
};
 
int main() {
  PCModle obj;
 
  std::thread ProducerThread = std::thread(&PCModle::producer_thread, &obj);
  std::thread ConsumerThread = std::thread(&PCModle::consumer_thread, &obj);
 
  ProducerThread.join();
  ConsumerThread.join();
 
  return 0;
}
```



## 共享内存

共享内存是进程间通信的一种方式。不同进程之间共享的内存通常为同一段物理内存，进程可以将同一段物理内存连接到他们自己的地址空间中，所有的进程都可以访问共享内存中的地址。如果某个进程向共享内存写入数据，所做的改动将立即影响到可以访问同一段共享内存的任何其他进程。

- 优点：访问高效，通信时无需内核接入避免不必要的复制
- 缺点：没有同步机制，需要手动设计



## 关闭中断的方式

Cortex-M3和M4中断屏蔽寄存器有三种

- PRIMASK
- FAULTMASK
- BASEPRI

1. PRIMASK寄存器设置为1后，关闭所有中断和除了HardFault异常外的所有其他异常，只有**NMI、Reset和HardFault可以得到响应**。

```assembly
CPSIE I;                                        // 清除PRIMASK（使能中断）
CPSID I;                                        // 设置PRIMASK（禁止中断）
```

2. FAULTMASK寄存器会把异常的优先级提升到-1，设置为1后关闭所有中断和异常，包括HardFault异常，只有**NMI和Reset可以得到响应**。

```assenbly
CPSIE F;                        // 清除FAULTMASK
CPSID F;                        // 设置FAULTMASK
```

3. BASEPRI寄存器可以屏蔽低于某一个阈值的中断。

设置为n后，屏蔽所有优先级数值大于等于n的中断和异常。Cortex-M的优先级数值越大其优先级越低。





## RT-Thread关闭中断

采用汇编代码实现，上述第一种关闭中断的方式，**屏蔽全部中断**，仅响应HardFault、NMI、Reset

rt_hw_interrupt_disable

```assembly
;/*
; * rt_base_t rt_hw_interrupt_disable();
; */
rt_hw_interrupt_disable    PROC
    EXPORT  rt_hw_interrupt_disable
    MRS     r0, PRIMASK
    CPSID   I
    BX      LR
    ENDP
```



## FreeRTOS关闭中断

```c
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY  // 此宏用来设置FreeRTOS系统可管理的最大优先级，也就是BASEPRI寄存器中存放的阈值。
// 关中断
// 向basepri中写入configMAX_SYSCALL_INTERRUPT_PRIORITY,
// 表明优先级低于configMAX_SYSCALL_INTERRUPT_PRIORITY的中断都会被屏蔽
static portFORCE_INLINE void vPortRaiseBASEPRI( void )
{
uint32_t ulNewBASEPRI = configMAX_SYSCALL_INTERRUPT_PRIORITY;

    __asm
    {
        msr basepri, ulNewBASEPRI
        dsb
        isb
    }
}
```



## RT-Thread rt_enter_critical()和rt_hw_interrupt_disable()区别

```c
rt_enter_critical()  //禁用调度器，不关闭中断，可嵌套调用，深度65535
rt_hw_interrupt_disable()  // 关闭中断，可嵌套调用
```



## FreeRTOS taskENTER_CRITICAL和taskDISABLE_INTERRUPTS区别

```c
vTaskSuspendAll()  // 挂起调度器。不关中断，属于 FreeRTOS 层面，不直接依赖具体的硬件，可嵌套调用
taskENTER_CRITICAL  // 支持嵌套调用，底层为关闭部分中断，有引用计数
taskDISABLE_INTERRUPTS  // 关闭中断，不支持嵌套，实现方式为配置BASEPRI寄存器，屏蔽某些中断
```

在下面例子中，调用funcA函数后，再执行完funcB函数后中断就会被打开，从而导致funcC()函数不会被保护。而若使用taskENTER_CRITICAL和taskEXIT_CRITICAL则不会出现这种情况。

```c
在临界区ENTER/EXIT内流程如下：
ENTER
  /* 中断DISABLE */
ENTER
EXIT
 /* 此时中断仍然DISABLE */
EXIT
 /* 释放所有的临界区,现在才会中断ENABLE*/
 
 
但在中断DISABLE内流程则是如下：
 
DISABLE
/* 现在是中断DISABLE */
DISABLE
 
ENABLE
/* 即使中断DISABLE了两次，中断现在也会重新使能 */
ENABLE
    
void funcA()
{
    taskDISABLE_INTERRUPT(); //关中断
    funcB();//调用函数funcB
    funcC();//调用函数funcC
    taskENABLE_INTERRUPTS();//开中断
}
 
void funcB()
{
    taskDISABLE_INTERRUPTS();//关中断
    执行代码
    taskENABLE_INTERRUPTS();//开中断
}
```



## FreeFTOS中断优先级设置

设置FreeRTOS系统可管理的最大优先级，也就是高于5的优先级（小于5的优先级），FreeRTOS不管。

```c
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY			15       //中断最低优先级(0-15)
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY	5        //系统可管理的最高中断优先级
```

![20190823151313168.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20190823151313168.png)



## 临界区

访问公共资源的程序片段，并不是一种通信方式。

进入临界区的两种方式

```c
taskENTER_CRITICAL();
{
    .............// 临界区，关闭中断
}
taskEXIT_CRITICAL();

vTaskSuspendAll();
{
    .............// 临界区，仅关闭调度器，但响应中断
}
xTaskResumeAll();
```



## 互斥锁Mutex、自旋锁Spin

当加锁失败时，互斥锁用「线程切换」来应对，自旋锁则用「忙等待」来应对

互斥锁：Mutex，独占锁，谁上锁谁有权释放，申请上锁失败后阻塞，不能在中断中调用

自旋锁：Spinlock：申请上锁失败后，一直判断是否上锁成功，消耗CPU资源，可在中断中调用



## 临界区与锁的对比

互斥锁与临界区的作用非常相似，但互斥锁（mutex）是可以命名的，也就是说它可以跨越进程使用。所以创建互斥锁需要的资源更多，所以如果只为了在进程内部使用的话使用临界区会带来速度上的优势并能够减少资源占用量。因为互斥锁是跨进程的互斥锁一旦被创建，就可以通过名字打开它

临界区是一种轻量级的同步机制，与互斥和事件这些内核同步对象相比，临界区是用户态下的对象，即只能在同一进程中实现线程互斥。因无需在用户态和核心态之间切换，所以工作效率比较互斥来说要高很多。

|        | 使用场景             | 操作权限           |
| ------ | -------------------- | ------------------ |
| 临界区 | 一个进程下不同线程间 | 用户态，轻量级，快 |
| 互斥锁 | 进程间或线程间       | 内核态，切换，慢   |



## 阻塞与非阻塞区别

阻塞：条件不满足时等待，进入阻塞态直到条件满足被唤醒

非阻塞：条件不满足时立刻返回，继续执行其他任务



## RTOS为何不用malloc和free

- 实现复杂，占用空间较多
- 并非线程安全操作
- 每次调用执行时间不确定
- 内存碎片化
- 不同编译器适配复杂
- 难以调试



## FreeRTOS内存管理算法

heap_1~5中除了heap_3分配在堆上，其余算法在bss段开辟静态空间进行管理

```c
// 定义内存堆的大小
#define configTOTAL_HEAP_SIZE (8 * 1024) // 8KB

// 全局变量 "uc_heap" 的定义
static uint8_t ucHeap[configTOTAL_HEAP_SIZE];
uint8_t *ucHeap = ucHeap;
```

[FreeRTOS笔记（六）：五种内存管理详解_CodeDog_wang的博客-CSDN博客](https://blog.csdn.net/weixin_43952192/article/details/108189300)

[FreeRTOS系列-- heap_4.c内存管理分析_为成功找方法的博客-CSDN博客](https://blog.csdn.net/yuanlin725/article/details/115087718)

| 类别   | 优点                 | 缺点                             |
| ------ | -------------------- | -------------------------------- |
| heap_1 | 时间确定             | 只分配，不回收                   |
| heap_2 | 最佳匹配             | 回收但不合并、时间不确定         |
| heap_3 | 使用标准malloc、free | 代码量大、线程不安全、时间不确定 |
| heap_4 | 最佳匹配、合并相邻   | 时间不确定                       |
| heap_5 | 支持多段不连续RAM    | 时间不确定                       |



1. **heap_1**

- 只分配不回收，不合并空闲区块

2. **heap_2**

- 使用最佳拟合算法分配
- 回收，但不合并，有碎片

3. **heap_3**

- 使用标准库malloc()和free()函数
- heap的大小由链接器配置定义（启动文件定义）

4. **heap_4**

- 使用first fit算法来分配内存
- 合并相邻的空闲内存块

![856ee0739f2c46798c2c3dc3c76ff4c8.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/856ee0739f2c46798c2c3dc3c76ff4c8.png)

5. **heap_5**

在heap_4的基础上，可以从多个独立的内存空间分配内存



## 内存池

内存池是一种用于管理和分配内存的技术。它被用于**解决频繁地申请和释放内存带来的性能问题**。

在传统的内存管理中，当需要使用内存时，通常会通过内存分配函数（如malloc）来动态申请一块内存空间。而释放内存时，则会调用相应的内存释放函数（如free）来释放内存。这种动态的内存分配和释放操作在频繁进行时，会产生很多开销，包括内存管理开销和内存碎片问题。

而内存池就是为了解决这个问题而设计的。它事先申请一定大小的内存空间，并将其划分成多个固定大小的块，形成一个池子。当需要使用内存时，直接从内存池中分配一个可用的块，而不是频繁地调用内存分配函数。在释放内存时，将内存块归还给内存池，而不是调用内存释放函数。

使用内存池的好处是可以降低内存碎片问题，减少动态内存分配和释放的开销。通过一次性申请和释放内存块，可以提高内存分配和释放的效率，从而提升程序性能。此外，内存池还可以提供内存分配的可预测性，**避免因动态内存分配造成的不确定性和性能抖动**。



## RT-Thread内存管理算法

RT-T开辟静态数组的方式管理内存

```c
#define RT_HEAP_SIZE 6*1024
/* 从内部SRAM申请一块静态内存来作为内存堆使用 */
static uint32_t rt_heap[RT_HEAP_SIZE];	// heap default size: 24K(1024 * 4 * 6)
```

| 算法          | 文件      | 说明                   | 例子                           |
| ------------- | --------- | ---------------------- | ------------------------------ |
| mem小内存     | mem.c     | 2MB以内小内存设备      | 一个瓜--吃多少切多少           |
| slab大内存    | slab.c    | 大内存设备，内存池管理 | 一个瓜--已经切好大小--拿对应的 |
| memheap多内存 | memheap.c | 多个内存设备进行合并   | 多个瓜--吃完一个拿下一个       |

1. mem小内存管理算法：heap_4

​		采用链表组织，每个表项包含{magic（是否被非法改写）,used（是否被使用）,next（指针域）,prev（指针域）}

​		分配64 Bye内存的操作：从表头开始，寻找可用空间进行分配（表头占用3*4 Byte）

​		释放的操作：更改used表项，查看前后是否为空闲，如有进行合并为大内存块

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221030102159893.png" alt="image-20221030102159893" style="zoom: 67%;" />

2. slab大内存管理算法：内存池

   为避免频繁分配释放，提前将内存分块

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221030103308568.png" alt="image-20221030103308568" style="zoom: 50%;" />

3. memheap内存管理算法：heap_5

   将多个不连续的内存地址进行合并拼接

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221030103522737.png" alt="image-20221030103522737" style="zoom:50%;" />

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221030103607395.png" alt="image-20221030103607395" style="zoom: 67%;" />



## RT-Thread 链表

普通双向循环链表（针对每一个数据结构固定的节点进行操作）

![watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70.png)

RTT中双向循环链表（数据结构不固定）

![watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70-16671148646223.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70-16671148646223.png)

RTT中链表不依赖于节点数据类型，其指针域指向下一个指针域（插入的元素可以为不同类型），

![watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70-16671149904816.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3kxNzU3NjU1Nzg4,size_16,color_FFFFFF,t_70-16671149904816.png)

指定节点前插入：

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/72204cdb118f4af4a61f4d004e53e8d6.png" alt="在这里插入图片描述" style="zoom:67%;" />

```c
rt_inline void rt_list_insert_before(rt_list_t *l, rt_list_t *n)
{
    l->prev->next = n;
    n->prev = l->prev;

    l->prev = n;
    n->next = l;
}
```

指定节点后插入：

![504f79b4ea524b65986891bd627b5586.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/504f79b4ea524b65986891bd627b5586.png)

```c
rt_inline void rt_list_insert_after(rt_list_t *l, rt_list_t *n)
{
    l->next->prev = n;
    n->next = l->next;

    l->next = n;
    n->prev = l;
}
```

删除节点：

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/3950e4591ce0431f9a04588f8ac0214e.png" alt="在这里插入图片描述" style="zoom:67%;" />

```c
rt_inline void rt_list_remove(rt_list_t *n)
{
    n->next->prev = n->prev;
    n->prev->next = n->next;

    n->next = n->prev = n;
}
```

节点元素的访问：

节点中，指针域的存放位置不确定，因此需要一种宏定义，从指针域寻找对应的结构体元素（通过rt_list_t成员的地址访问节点中的其他元素）

既然`rt_list_t`成员是存放在节点中部或是尾部，且不同类型的节点`rt_list_t`成员位置还不一样，那在遍历整个链表时，获得的是后继节点（前驱节点）的`rt_list_t`成员的地址，那如何根据`rt_list_t`成员的地址访问节点中其他元素。
  尽管不同类型节点中`rt_list_t`成员位置不定，但是在确定类型节点中，`rt_list_t`成员的偏移是固定的，在获取`rt_list_t`成员地址的情况下，计算出`rt_list_t`成员在该节点中的偏移，即(`rt_list_t`成员地址)-(`rt_list_t`成员偏移）=节点起始地址。关键在于如何计算不同类型节点中`rt_list_t`成员偏移。RT-Thread中给出的相应算法如下：

```c
/**
 * Double List structure
 */
struct rt_list_node
{
    struct rt_list_node *next;                          /**< point to next node. */
    struct rt_list_node *prev;                          /**< point to prev node. */
};
typedef struct rt_list_node rt_list_t;                  /**< Type for lists. */
```

```c
struct rt_thread
{
    char        name[RT_NAME_MAX];                      /**< the name of thread */
    rt_list_t   list;                                   /**< the object list */
    rt_list_t   tlist;                                  /**< the thread list */
    rt_uint8_t  current_priority;                       /**< current priority */
    rt_uint8_t  init_priority;                          /**< initialized priority */
};
typedef struct rt_thread *rt_thread_t;

#define rt_container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - (unsigned long)(&((type *)0)->member)))

//ptr: 成员首地址（指针域地址，例如 rt_thread_priority_table[highest_ready_priority].next）
//type: 结构体类型（例如 struct rt_thread）
//member: 结构体成员名称（例如 tlist）
```



## RT-Thread 抢占式调度实现

两个线程，低优先级`t2`任务while(1)执行耗时任务，高优先级`t1`任务抢占式打印随后阻塞

调度器执行顺序：

​		1.高优先级任务先执行，执行到`rt_thread_mdelay()`调用`rt_thread_sleep()`中的`rt_schedule()`挂起

​		2.调度器介入，寻找到当前最高优先级任务（`t2`）运行

​		3.低优先级任务时间片未到情况下，由于高优先级任务`rt_thread_mdelay()`超时，其定时计数器变化

​		4.下一个节拍周期到达，定时执行`rt_tick_increase()`，调用`rt_timer_check()`中的`timeout_func()`

​		5.由函数指针跳转到`rt_thread_timeout()`，执行其中的`rt_schedule()`

​		6.进入PendSV中断处理函数进行线程上下文切换



## FreeRTOS内存管理

FreeRTOS的内存位于.bss段，并非heap（启动文件中的堆空间大小）

使用`pvPortMalloc`函数申请内存时，也是从这个系统堆（实际为bss段）中申请的

```c
#define configTOTAL_HEAP_SIZE                        ( ( size_t ) ( 100 * 1024 )   // 申请100KB内存用于RTOS系统堆内存
```

在map文件中可以看到FreeRTOS使用一个静态数组作为HEAP，以我使用的`heap_4.c`内存管理策略来说，它定义在`heap_4.c`这个文件里面。因为这个HEAP来自于静态数组，所以它存在于数据段(具体为.bss段)，并不是我一开始认为的FreeRTOS所使用的HEAP来自于系统的堆。

```c
.bss                  zero     0x2021'7d1c  0x1'9000  heap_4.o [35]  // 实际位于.bss段

Entry                       Address      Size  Type      Object
-----                       -------      ----  ----      ------
ucHeap                  0x2021'7d1c  0x1'9000  Data  Lc  heap_4.o [35]  // 起始地址与大小
```





## FreeRTOS任务调度

- 系统时钟判断最高优先级任务进行调度
- 当前任务主动执行taskYIELD()或portYIELD_FROM_ISR()让出CPU使用权



## FreeRTOS创建任务

在堆中通过pvPortMalloc分配内存给TCB



## 任务堆栈

在创建任务时，可以选择动态创建或静态创建，静态的任务栈在任务结束后无法被回收，动态的可以

![d5276c09e3fed20db0a9025f8a0b755d.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/d5276c09e3fed20db0a9025f8a0b755d.png)



## RTOS堆栈溢出的检测

方案1：在调度时检查栈指针是否越界（任务保存有栈顶和栈大小信息，每次切换时检查栈指针是否越界）

- 优点：检测较快
- 缺点：对于任务运行时溢出，而切换前又恢复正常的情况无法检测

方案2：在调度时检查栈末尾的16个字节是否发生改变（创建任务时初始化为特定字符，每次切换时判断是否被改写）

- 优点：可检出几乎所有溢出
- 缺点：检测较慢



## RT-Thread PendSV系统调用--上下文切换

省流版：**OS调度依赖于systick，最低优先级，ISR抢占OS调度先执行，OS调度在无ISR时实际由PendSV执行，若在调度时ISR到来那么插队执行ISR，再调度**

一、方法1-无PendSV-SysTick最高优先级（Fault异常）：

- 假如在产生异常时，CPU正在响应另一个中断ISR，而SysTick的优先级又大于ISR，在这种情况下，SysTick就会抢占ISR，获取CPU使用权，但是在SysTick中不能进行上下文切换，因为这将导致中断ISR被延迟，这在实时要求的系统中是不能容忍的，并且由于**IRQ未得到响应，执行了线程，触发Fault异常**。

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/985d1f704b714f0db46dc11aea1d6516.png" alt="在这里插入图片描述" style="zoom:67%;" />

二、方法2-无PendSV-SysTick最低优先级（无法满足实时）：

- 将SysTick的优先级设置为最低，然后在SysTick中进行上下文切换
- 一般OS在调度任务时，会**关闭中断**，也就是进入临界区，而OS任务调度是要耗时的，这就会出现一种情况：
    在任务调度期间，如果新的外部IRQ发生，CPU将不能够快速响应处理。

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/ce65afff54074fb4b1c11c581cdab6a9.png" alt="在这里插入图片描述" style="zoom:67%;" />



三、PendSV-SysTick最低优先级（实际方案）

- 将SysTick的优先级调低，避免了触发Fault的问题，但是会影响外部中断IRQ的处理速度，那有没有进一步优化的方法呢？答案就是PenSV。因为PendSV有【缓期执行】的特点，所以可以将上图中的OS拆分，分成2段：

1. 滴答定时器中断，制作业务调度前的判断工作，不做任务切换。
2. 触发PendSV，PendSV并不会立即执行，因为PendSV的优先级最低，如果此时正好有IRQ请求，那么先响应IRQ，最后等到所有优先级高于PendSV的IRQ都执行完毕，再执行PendSV，进行任务调度。（PendSV可被打断）

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/8619359f18254c73bbdcfe7f524fc9e1.png" alt="在这里插入图片描述" style="zoom:67%;" />

实际方案的缺陷：（系统节拍被ISR打乱）

1. SysTick的优先级最低，那如果外部IRQ比较频繁，是不是会导致SysTick经常被挂起，然后滞后，导致Systick的节拍延长，进而导致不准啊？
2. 因为1的原因，导致任务的执行调度就不够快了？



四、若将SysTick设置最高优先级，保证系统节拍（实时性不足，无法响应ISR）

- 这样似乎解决了问题，但是又带来了一个问题，SysTick的优先级最高，而且又是周期性的触发，会导致经常抢占外部IRQ，这就会导致外部IRQ响应变慢，

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/183197e37e1146a09eb1012a48ba0f37.png" alt="在这里插入图片描述" style="zoom:67%;" />



实际方案：

1. 滴答定时器中断，制作业务调度前的判断工作，不做任务切换。
2. 触发PendSV，PendSV并不会立即执行（优先级最低），如果此时正好有IRQ请求，那么先响应IRQ，最后等到所有优先级高于PendSV的IRQ都执行完毕，再执行PendSV，进行任务调度。

​		具体实现流程：

​				1.任务A请求SVC（supervisor call，系统调用）进行任务切换

​				2.内核收到请求，挂起PendSV异常

​				3.CPU退出SVC后进入PendSV，执行上下文切换

​				4.PendSV执行完毕后返回任务B

​				5.中断发生，执行ISR（子中断服务程序）

​				6.ISR执行中，心跳到达，SysTick异常发生，抢占了ISR

​				7.PendSV准备进行上下文切换

​				8.SysTick退出后，继续执行ISR

​				9.ISR执行完毕，进入PendSV进行上下文切换

​				10.切换至任务A

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/10pendsv.jpg" alt="PendSV 中断处理" style="zoom:80%;" />



## SVC中断

SVC（系统服务调用）和 PendSV（ 可悬挂系统调用 ）。

它们多用于在操作系统之上的软件开发中。
SVC 用于产生系统函数的调用请求。
例如，操作系统不让用户程序直接访问硬件，而是通过提供一些系统服务函数，用户程序使用 SVC 发出对系统服务函数的呼叫请求，以这种方法调用它们来间接访问硬件。因此，当用户程序想要控制特定的硬件时，它就会产生一个 SVC 异常，然后操作系统提供的 SVC 异常服务例程得到执行，它再调用相关的操作系统函数，后者完成用户程序请求的服务。

![20200807100320959.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20200807100320959.png)

系统调用处理异常，用户与内核进行交互，用户想做一些内核相关功能的时候必须通过SVC异常，让内核处于异常模式，才能调用执行内核的源码。触发SVC异常，会立即执行SVC异常代码。

为什么要用SVC启动第一个任务？因为使用了OS，任务都交给内核。总不能像裸机调用普通函数一样启动一个任务。



FreeRTOS中任务调度器触发了 `SVC` 中断来启动第一个任务，之后的工作都靠 `PendSV` 和 `SysTick` 中断触发来实现

`SVC`是系统服务调用，由 `SVC` 指令触发调用。在 [FreeRTOS](https://so.csdn.net/so/search?q=FreeRTOS&spm=1001.2101.3001.7020) 中用来在任务调度中开启第一个任务。触发指令：svc 0

- `SVC`中断就是软中断，给用户提供一个访问硬件的接口
- `PendSV`中断相对`SVC`来说，是可以被延迟执行的，用于任务切换



## FreeRTOS中_FROM_ISR

作用：在中断中调用的API，其禁用了调度器，无延时等阻塞操作，保证临界区资源快进快出访问

RT-Thread中没有类似的API，仅有延时参数选项



## RT-Thread 同步互斥与通信

| 内核对象      | 生产者 | 消费者    | 数据/状态  | 说明                               |
| ------------- | ------ | --------- | ---------- | ---------------------------------- |
| Semaphore     | all    | all       | 数量0~n    | 维护的资源个数                     |
| Mutex         | A上锁  | 只能A开锁 | bit 0、1   | 单一互斥资源                       |
| Event         | all    | all       | 多个bit    | 传递事件用以唤醒，实现多任务的同步 |
| Mail box      | all    | all       | 固定4 Byte | 传递指针                           |
| Message queue | all    | all       | 若干数据   | 传递数据（结构体）                 |
| Signal        |        |           |            | 软中断，用以唤醒                   |



## RT-Thread 消息队列、邮箱、信号量区别

全局变量通信：可以承载通信的内容，但无法告接收方知数据的到达（需要接收方轮询，占用资源）

信号量：告知接收方信息到达，但是未告知数据内容

消息队列：承载了信息内容，同时告知接收方信息到达

邮箱：4 Byte的通信，通过指针而非memcpy()，开销小



## RTOS优先级的分配原则

依据任务对响应的敏感性、执行时长（RTOS抢占式，会导致饥饿）

串口接收中断等任务优先级最高

电机PID计算以及控制需要固定控制周期，优先级较高

看门狗，按键处理中等、

最低的APP层的心跳和信息显示任务



## FreeRTOS优先级

高优先级数字大



## 优先级反转

使用信号量时

高优先级任务被低优先级任务阻塞，导致高优先级任务迟迟得不到调度。但其他中等优先级的任务却能抢到CPU资源。-- 从现象上来看，好像是中优先级的任务比高优先级任务具有更高的优先权。

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/mutex002.png" alt="查看源图像" style="zoom: 50%;" />



## RT-Thread内核移植

CPU架构移植：

​		在不同的架构，如RISC-V、Cortex-M上运行，上下文切换，时钟配置以及中断操作等的适配

BSP移植：

​		对于同架构CPU，对不同外设进行适配、动态内存管理



## RT-Thread POSIX标准

Portable operating system interface，保证应用程序在不同OS下的可移植性



## RT-Thread单元测试

定义：对软件中的最小可测试单元进行检查和验证（函数、方法、类、功能模块）

utest框架（unit test）



## RT-Thread 崩溃调试

`CmBacktrace` 函数，崩溃后保存线程栈和寄存器值，可逆向分析调用关系

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221204193728105.png" alt="image-20221204193728105" style="zoom: 50%;" />

## RTOS中多线程看门狗

方案1：在最低优先级线程喂狗，若高优先级线程长时间抢占，则看门狗超时

方案2：监控各线程调度情况，每个线程放置定时任务喂狗，超时则单个线程阻塞