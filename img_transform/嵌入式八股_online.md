以下内容为本人面试真题总结，为rmer和群友专供。

主要知识点：RTOS、总线、控制、STM32（传统电控技术栈）

有疑问请联系qq：1296828054

注：如果有误可以联系我更改。

# FreeRTOS 相关

## 1.FreeRTOS 任务调度的简要过程

**FreeRTOS 任务调度是指 FreeRTOS 内核根据任务的优先级和状态来决定何时运行哪个任务**。

[FreeRTOS深入教程（任务创建的深入和任务调度机制分析）_freertos教程-CSDN博客](https://blog.csdn.net/m0_49476241/article/details/133973941)

1. ***\*任务创建：\****在 FreeRTOS 中，通过调用 xTaskCreate() 或类似函数创建任务。
2. ***\*确定初始运行任务：\****FreeRTOS 在启动时会自动**启动空闲任务**，它负责管理系统中没有其他可运行任务时的情况。
3. ***\*调度器启动：\****调度器负责根据各个任务的优先级和状态来进行合适的上下文切换。然后SVC中断。
4. ***\*抢占式调度：\****FreeRTOS 使用基于优先级的抢占式调度算法。当更高优先级的就绪状态任务准备好运行时，当前正在运行的低优先级任务将被暂停，并且控制权转移到高优先级任务。
5. ***\*时间片轮转：\****当任务优先级相等时采用。操作系统为每个任务分配一个时间片，即预定义的时间量。在时间片轮转调度方式下，每个任务可以执行一个时间片，然后系统将控制权移交给下一个就绪的任务。**如果一个任务在其时间片结束前没有完成，系统会暂停该任务，将控制权交给下一个就绪的任务**。这种调度方式有助于确保任务之间的公平性，避免某些任务长时间占用处理器，同时允许多个任务分享处理时间。
6. ***\*任务A阻塞：\****调用OSDelay或者vTaskDelay阻塞。
7. ***\*保存任务A的上下文：\****`PendSV`中断用于执行上下文切换，被`SysTick`中断或`osdelay`主动出发触发，优先级最低。
8. ***\*选择下一个任务：\****`PendSV` 中断服务程序会调用 `vTaskSwitchContext` 函数。这个函数是 FreeRTOS 的核心调度函数，它负责选择下一个将要运行的任务，并更新当前任务控制块（TCB）指针 `pxCurrentTCB`。
9. ***\*恢复任务B的上下文：\****
10. ***\*延迟与阻塞：\****FreeRTOS 允许在等待事件发生或特定条件满足时使得一个或多个线程进入延迟或阻塞状态，并在条件满足后重新激活这些线程。

### 任务运行示例(时间片+优先级)

`configUSE_PREEMPTION`优先级抢占宏 `configUSE_TIME_SLICING`时间片轮询宏

A = 10ms，B= 0.5ms

| 优先级 | 执行顺序                                                     | 结论                                                         |
| ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| A > B  | A(10ms)  ----->osdelay()----->B(0.5ms)------>osdelay()----->A(10ms)![image-20240702022858910.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240702022858910.png) | AB都完整运行,B频率低                                         |
| A < B  | B(0.5ms)------>osdelay()----->A(0.5ms)被打断------->systick()---->B(0.5ms)![image-20240702022926610.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240702022926610.png) | A会被B打断，A频率低                                          |
| A = B  | B(0.5ms)------>osdelay()----->A(1ms)时间片------>systick()----->B(0.5ms)![image-20240702022926610.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240702022926610.png) | 时间片轮询，如果B没有调用挂起，则需要等待时间片耗尽。如果调用阻塞，则在阻塞后立刻切换到A |

### Freertos链表

**任务列表数组的每一个元素是一个链表，链表中的节点关联到TCB。**

**1.就绪链表（Ready List）**
就绪链表包含所有处于就绪状态的任务。就绪状态的任务是指已经准备好运行，但由于当前执行的任务正在占用 CPU 资源，它们暂时无法立即执行。这些任务按照优先级被组织在就绪链表中。当当前正在执行的任务释放 CPU（例如，由于时间片用完、任务阻塞或挂起等原因）时，调度器从就绪链表中选择优先级最高的任务来执行。

**2.阻塞链表（Blocked List）**
阻塞链表包含那些由于某种原因而无法立即执行的任务。这些原因可能包括等待某个事件、资源不可用、延时等情况。当任务处于阻塞状态时，它们不会被调度器所执行。这些任务会在特定条件满足之后重新放入就绪链表，等待调度器选择其执行。

**3.挂起链表（Suspended List）**
挂起链表包含已被显式挂起的任务。当任务被挂起时，它们暂时停止运行，不再参与调度。这些任务不会出现在就绪链表或阻塞链表中，因为它们被明确地挂起，不参与任务调度。![image-20240702181811152.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240702181811152.png)
[深入理解FreeRTOS_学习笔记(10.链表)_freertos链表-CSDN博客](https://blog.csdn.net/m0_65525149/article/details/130986152)

### 确定下一个运行的任务

- **位图**，表示哪些优先级有就绪任务。每个位对应一个优先级，如果某一位为1，表示该优先级有任务就绪。硬件加速，CLZ指令查找
  **前导0**（第一个1前0的个数），获取最高优先级列表。
- 任务列表数组，每个数组元素是一个链表，链表中的每个节点代表一个特定优先级的就绪任务。遍历查找



### 优先级翻转

使用信号量时。（互斥量、信号量、队列）

高优先级任务被低优先级任务阻塞，导致高优先级任务迟迟得不到调度。但其他中等优先级的任务却能抢到CPU资源。-- 从现象上来看，好像是中优先级的任务比高优先级任务具有更高的优先权。

![mutex002.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/mutex002.png)

- FreeRTOS 的**优先级继承机制**是一种用于解决优先级反转问题的手段。
- 低优先级任务占用资源的时候加锁，高优先级用的时候发现被锁了就把低优先级的优先级提高。

**优先级继承机制的工作原理**

1. **资源请求**：高优先级任务尝试获取一个被低优先级任务持有的互斥锁。
2. **优先级提升**：如果高优先级任务发现互斥锁被低优先级任务持有，FreeRTOS 会将低优先级任务的优先级提升到与高优先级任务相同的级别。这保证了低优先级任务能够尽快完成对资源的使用。
3. **资源释放**：当低优先级任务释放互斥锁时，它的优先级会恢复到原来的级别。
4. **调度**：高优先级任务可以获取互斥锁并继续执行。





## 2.每个任务有自己的东西

**每个任务的关键组成部分**

1. **任务控制块（TCB，Task Control Block）**：
   - 每个任务都有一个TCB，包含该任务的所有信息，如任务状态、优先级、任务堆栈的起始地址和当前堆栈指针等。
   - TCB在FreeRTOS中用于管理和调度任务。
2. **任务堆栈**：
   - 每个任务都有自己的堆栈空间，用于存储局部变量、函数调用返回地址和任务上下文（CPU寄存器的值）。
   - 堆栈空间是在创建任务时从共享内存（通常是SRAM）中分配的。
   - 采用heap4内存管理，分配的堆栈是连续的。

**共享内存和堆栈分配**

虽然STM32的内存是共享的，但任务堆栈的分配是通过分配内存区域来实现的，每个任务在创建时从共享内存中分配一块独立的堆栈空间。这种分配通常由FreeRTOS的内存管理函数（如`pvPortMalloc`）处理。

## 3.SVC中断和PendSV

- **SVC（Supervisor Call）**：
  - `SVC`中断就是软中断，给用户提供一个访问硬件的接口。
  - 主要用于启动第一个任务。
  - 通过 `svc` 指令触发并进入 SVC 异常处理程序。
- **PendSV（Pendable Service Call）**：
  - 专门用于任务上下文切换。
  - 被SysTick和taskyeild中断触发，优先级最低，在调度器需要切换任务时触发。
  - 通过设置 NVIC 的 PendSV 位触发，并在异常处理程序中保存和恢复任务上下文。

### SVC

SVC 用于产生系统函数的调用请求。
**当用户程序想要控制特定的硬件时，它就会产生一个 SVC 异常**，然后操作系统提供的 SVC 异常服务例程得到执行，它再调用相关的操作系统函数，后者完成用户程序请求的服务。

![20200807100320959.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20200807100320959.png)

系统调用处理异常，用户与内核进行交互，用户想做一些内核相关功能的时候必须通过SVC异常，让内核处于异常模式，才能调用执行内核的源码。**触发SVC异常，会立即执行SVC异常代码**。

```c
void triggerSVC(void)
{
    __asm volatile ("svc 0");
}
```

**FreeRTOS中任务调度器触发了 `SVC` 中断来启动第一个任务，之后的工作都靠 `PendSV` 和 `SysTick` 中断触发来实现**

为什么要用SVC启动第一个任务？因为使用了OS，任务都交给内核。总不能像裸机调用普通函数一样启动一个任务。

### PendSV

`PendSV` 中断就是一个用来处理上下文切换的中断，可以由多种方式触发：

1. **`SysTick` 定时器中断**：这是最常见的触发方式，用于实现时间片轮转调度。
2. **其他中断**：其他中断处理程序也可以根据需要显式触发 `PendSV` 中断。
3. **任务调用**：任务本身也可以通过调用 `taskYIELD()` 或其他调度相关函数来触发 `PendSV` 中断。`osdelay`也可以触发，在阻塞任务的过程中，会将调度器先挂起，然后进行移动任务到阻塞链表的操作，再恢复调度器。恢复调度器后会自动检查是否需要进行任务切换，会触发`portYIELD_WITHIN_API`进行上下文切换。



## 4.上下文切换

当操作系统决定暂停当前正在执行的任务并开始执行另一个任务时，就会发生上下文切换。

**上下文切换的内容：**

1. **通用寄存器**：R0-R12
2. **堆栈指针**：PSP
3. **程序计数器**：PC
4. **链接寄存器**：LR
5. **程序状态寄存器**：xPSR
6. **浮点寄存器**

**切换步骤：**

1. 保存当前任务的上下文

2. 选择要运行的下一个任务

3. 加载新任务的上下文

4. 更新调度器状态

5. 执行新选定的任务

   

## 5.FreeRTOS中_FROM_ISR

作用：在中断中调用的API，其禁用了调度器，无延时等阻塞操作，保证临界区资源快进快出访问



## 6.中断和任务的关系

**中断和任务是操作系统处理并发性的两种基本机制。**

***\*中断：\****

- 中断通常由硬件设备（如定时器、外部设备）或软件请求（如系统调用）触发。

- 中断会暂停当前正在执行的程序，保存其上下文，并跳转到一个称为中断服务程序（ISR），完成后恢复程序继续执行。

- FreeRTOS 允许用户编写中断服务程序（ISR），用于响应硬件事件或外部触发的中断。
- 中断服务程序通常需要尽可能快速地完成执行，以便尽快恢复正常任务调度。

***\*任务：\****

- 任务是操作系统调度和管理的基本执行单元，通常指线程（Thread）或进程（Process）。

- FreeRTOS 通过调度器负责管理和调度多个任务，并确保它们按照优先级和就绪状态正确执行。
- 每个任务都有自己的堆栈空间、上下文信息等，由调度器进行管理。

***\*关系：\****

- 并发性：中断允许在某些事件发生时及时响应，而任务则允许多个代码块同时运行。

- 中断服务程序可能需要与任务进行通信或共享数据。这种情况下需要谨慎设计数据共享和同步机制。
- 中断可以唤醒阻塞状态下的任务，例如通过发送信号量或使用消息队列通知等机制。
- 任务可以在其执行过程中禁用某些中断（通过临界区保护）以确保关键代码段不被打断。

***\*FreeRTOS 中的应用：\****

- 中断通常用于处理硬件事件（如定时器、外设输入输出等），而任务用于实现更复杂的功能模块或业务逻辑。


***\*资源共享与同步：\****

- 在 FreeRTOS 中，需要注意在中断服务程序和任务之间共享资源时可能出现竞态条件问题。

- 可以使用信号量、消息队列等机制来实现资源共享和同步，在避免数据竞争方面起到重要作用。




## 7.高优先级打断低优先级中断

### NVIC

- NVIC（嵌套向量中断控制器）NVIC 是 ARM Cortex-M 系列处理器的一部分**是一种硬件结构**。
- NVIC 通过**中断向量表来管理中断**。
- 当中断发生时，处理器会根据**中断号从向量表中获取相应的中断服务程序地址**，然后开始执行相应的中断处理程序。
- NVIC 还负责中断优先级的管理，它可以根据**中断类型和配置的优先级来确定哪个中断应该被优先处理**。

### 中断抢占

当一个低优先级中断正在执行时，如果有一个高优先级的中断触发。通常会发生以下情况：

***\*1. \*\*中断抢占\*\*：\****当一个高优先级的中断触发时，如果其优先级高于当前正在执行的低优先级中断，处理器会立即中断当前正在执行的低优先级中断，并且开始执行高优先级中断的中断服务程序。这使得高优先级的中断能够迅速响应，保证了系统对重要事件的及时处理。

***\*2. \*\*中断嵌套\*\**\***：在一些处理器中，包括使用 NVIC 的 ARM Cortex-M 系列处理器，支持中断嵌套。这意味着当高优先级中断发生时，它可以抢占正在执行的低优先级中断，并执行其自己的中断服务程序。但是，一旦高优先级中断处理完毕，处理器会返回到被抢占的低优先级中断处继续执行。



## 8.任务调度通过SysTick进行

通过系统定时器中断触发。在ARM Cortex-M基础上的实现中，例如STM32微控制器，FreeRTOS通常使用**SysTick**定时器来生成操作系统节拍。SysTick是Cortex-M内核提供的一个系统定时器，专门设计用来支持操作系统。

 

## 9.消息队列

***\*### 消息队列的基本概念\****

消息队列允许一个或多个任务发送（写入）消息到队列中，而一个或多个任务可以从队列中接收（读取）消息。每个消息队列都有一个固定的长度，既可以存储固定数量的消息，也可以存储固定大小的数据项。

***\*### 如何创建消息队列\****

在FreeRTOS中，使用`xQueueCreate()`函数来创建一个新的消息队列。这个函数需要两个参数：队列可以容纳的最大消息数以及每个消息的大小（字节为单位）。

```c
QueueHandle_t xQueueCreate(UBaseType_t uxQueueLength, UBaseType_t uxItemSize);
```

\- `uxQueueLength` 是队列中可以保存的最大消息数。

\- `uxItemSize` 是队列中每个消息的大小（以字节为单位）。

***\*### 发送消息到队列\****

向队列发送消息可以使用`xQueueSend()`、`xQueueSendToFront()`、`xQueueSendToBack()`或`xQueueSendFromISR()`（从中断服务例程中发送）等函数。这些函数允许将消息放入队列的尾部或头部。

```c
BaseType_t xQueueSend(QueueHandle_t xQueue, const void * pvItemToQueue, TickType_t xTicksToWait);
```

\- `xQueue` 是消息队列的句柄。

\- `pvItemToQueue` 是指向要发送的消息的指针。

\- `xTicksToWait` 是任务在消息可以发送到队列之前愿意等待的时间（以节拍为单位）。

***\*### 从队列接收消息\****

从队列接收消息可以使用`xQueueReceive()`函数，它从队列中取出最早的消息。

```c
BaseType_t xQueueReceive(QueueHandle_t xQueue, void *pvBuffer, TickType_t xTicksToWait);
```

\- `xQueue` 是消息队列的句柄。

\- `pvBuffer` 是指向接收消息的缓冲区的指针。

\- `xTicksToWait` 是任务在接收到消息之前愿意等待的时间（以节拍为单位）。

**\#示例**

假设有一个任务负责读取传感器数据，另一个任务负责处理这些数据。可以创建一个消息队列，传感器读取任务将数据发送到队列，而数据处理任务从队列接收数据。

```c
// 创建消息队列
QueueHandle_t xQueue = xQueueCreate(10, sizeof(int));
// 发送数据到队列
int sensorData = 123;
if(xQueueSend(xQueue, &sensorData, (TickType_t)10) != pdPASS) {
  // 处理发送失败的情况
}

// 从队列接收数据
int receivedData;
if(xQueueReceive(xQueue, &receivedData, (TickType_t)10) == pdPASS) {
  // 使用接收到的数据
}
```

***\*使用消息队列的中断安全函数\****

由于在中断上下文中不能使用标准的队列操作函数（如xQueueSend或xQueueReceive），FreeRTOS 提供了特别设计用于从ISR中调用的函数。这些函数的名字通常以FromISR后缀结尾，例如：

```c
xQueueSendFromISR()

xQueueSendToFrontFromISR()

xQueueSendToBackFromISR()

xQueueReceiveFromISR()
```





## 10.消息队列和共享内存的区别是什么，消息队列是如何做防止两个任务同时使用的

***\*消息队列和共享内存是两种常见的进程或任务间通信（IPC）机制\****，它们在用途、实现和适用场景上有显著的区别。选择哪种机制取决于应用的具体需求，包括数据传输的复杂性、同步需求、性能考虑等因素。

***\*### 消息队列\****

消息队列是一个先入先出（FIFO）的数据结构，用于存储待处理的消息。进程或任务可以将消息发送到队列，其他进程或任务可以从队列接收消息。消息队列提供了一种松耦合的通信方式，发送者和接收者不需要同时在线，也不需要直接知道对方的存在。

***\**\*优点\*\*：\****

\- **同步与异步通信**：支持同步和异步消息传递。

\- **松耦合**：发送者和接收者之间的松耦合使得系统组件更容易管理和维护。

\- **消息传递**：可以跨不同进程安全地传递复杂的数据结构。

***\**\*缺点\*\*：\****

\- **性能开销**：每条消息的发送和接收都涉及到系统调用，可能比共享内存方式更慢。

\- **资源限制**：系统对可用消息队列的数量和大小可能有限制。

***\*### 共享内存\****

共享内存允许两个或多个进程共享一个给定的存储区，是最快的IPC方法之一。所有共享内存的进程都可以直接读写这块内存。

***\**\*优点\*\*：\****

\- **性能**：因为数据不需要在进程间复制，所以共享内存通常提供了最高的数据传输速率。

\- **直接访问**：进程可以直接对内存进行读写操作，减少了中间层的开销。

***\**\*缺点\*\*：\****

\- **同步复杂性**：当多个进程需要访问共享内存时，需要额外的同步机制（如互斥锁、信号量等）来防止数据竞态和一致性问题。

\- **安全性和健壮性**：不当的内存访问可能导致数据损坏或程序崩溃。

***\*### 防止同时使用\****

消息队列自身通过内部的锁（如互斥锁）和同步机制来保证在任一时刻只有一个任务能够对其进行操作，从而避免了并发访问的问题。发送和接收消息的操作通常是原子的，操作系统确保了消息的完整性和队列的状态一致性。

共享内存区别于消息队列，在于它不提供内建的同步机制。使用共享内存时，开发者需要使用其他同步工具，如信号量或互斥锁，来防止多个进程同时访问内存区域，确保数据一致性和防止竞态条件。

***\*### 总结\****

选择消息队列还是共享内存取决于具体的应用场景。如果IPC涉及复杂的数据结构或者需要保证通信双方的解耦，消息队列可能是更好的选择。如果性能是首要考虑因素，并且开发者可以妥善管理同步问题，共享内存可能是更合适的选择。在实际应用中，这两种机制有时会结合使用，以达到既快速又可靠的通信。

 

## 11.消息队列，传入和传出时发生了什么

***\*消息队列\****是一种重要的进程间通信（IPC）机制，允许进程或线程安全地交换信息。这种机制通过在内存中创建一个队列来实现，进程可以向队列中添加消息，并从中读取消息。

***\*传入（发送）消息时发生了什么\****

1. **消息序列化**：如果消息不是原始二进制形式，它首先被序列化或打包成一种标准格式，以便安全地通过队列传输。这对于复杂的数据结构或跨语言通信尤其重要。
2. **队列访问**：发送进程通过操作系统API请求向指定的消息队列发送消息。如果队列实现了访问控制，操作系统将验证进程是否有权写入队列。
3. **消息排队**：操作系统将消息放入队列的尾部。如果队列设置了消息优先级，系统会根据优先级将消息插入到适当的位置。
4. **阻塞和超时**：如果队列已满，发送进程可能会根据API调用的具体参数被阻塞，直到队列中有足够的空间为止，或者操作超时。
5. **通知接收者**：一旦消息被成功排队，操作系统可能会通知一个或多个等待接收消息的进程，告知它们现在队列中有消息可用。

***\*### 传出（接收）消息时发生了什么\****

1. **队列访问**：接收进程通过操作系统API请求从消息队列中读取消息。和发送过程一样，如果实现了访问控制，将进行权限检查。

2. **消息检索**：操作系统从队列的头部检索消息，如果队列是空的，接收进程根据API调用的参数可能会阻塞，直到有消息到达，或者操作超时。

3. **消息反序列化**：接收到的消息如果需要，将被反序列化或解包，转换回适用于接收进程的数据结构。

4. **确认处理**：在某些系统中，接收进程可能需要显式确认它已成功处理消息，特别是在需要消息可靠性的场景中。这样可以允许系统在消息未成功处理时重试传递。

5. **资源管理**：消息被成功接收并处理后，相关的系统资源（如内存）将被回收，以便再次使用。

   

## 12.临界区

在 FreeRTOS 中，临界区的作用是确保某段代码在执行过程中不会被中断或调度器切换到其他任务，从而保护共享资源免受并发访问的影响。不是一种通信。

进入临界区的两种方式

```c
taskENTER_CRITICAL();
// 代码
taskEXIT_CRITICAL();

vTaskSuspendAll();
//代码
xTaskResumeAll();
```

**临界区应尽可能小**：进入临界区会禁止中断或暂停调度，这可能会影响系统的实时性和响应性。因此，临界区应尽可能小，只保护必要的代码段。

**避免在临界区中调用可能阻塞的函数**：在临界区中调用可能阻塞的函数（如等待信号量、消息队列等）会导致系统死锁或任务调度问题。

**选择合适的方法**：全局中断禁止的临界区适用于需要保证极高安全性的场合，但会影响所有中断；调度器暂停的方法更温和，只会影响任务调度，不会影响中断处理。

### 什么时候使用临界区

1. **访问共享硬件资源**：多个任务需要访问同一个硬件外设（例如 UART、I2C、SPI 等）。
2. **操作共享数据结构**：多个任务需要操作同一个链表、队列或其他复杂数据结构。
3. **更新全局配置**：多个任务可能需要读取和更新全局配置参数。

**示例：任务间共享一个全局变量**

假设有两个任务 `Task1` 和 `Task2`，它们共享一个全局变量 `counter`。如果不使用临界区，在某些情况下可能会导致数据竞争，导致 `counter` 的值不正确。

**不使用临界区的情况**

```c
int counter = 0;

void Task1(void *pvParameters) {
    while (1) {
        counter++;
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void Task2(void *pvParameters) {
    while (1) {
        counter--;
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

在这个例子中，`Task1` 和 `Task2` 都在对 `counter` 进行操作。由于 `counter++` 和 `counter--` 不是原子操作，可能会发生以下情况：

- `Task1` 读取 `counter` 的值。
- 任务切换到 `Task2`，`Task2` 修改 `counter` 的值。
- 再次切换回 `Task1`，`Task1` 使用过时的 `counter` 值进行加操作。

这种情况会导致 `counter` 的值不正确。

**使用临界区的情况**

为了避免上述问题，我们可以在访问 `counter` 时使用临界区：

```c
int counter = 0;

void Task1(void *pvParameters) {
    while (1) {
        taskENTER_CRITICAL();
        counter++;
        taskEXIT_CRITICAL();
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void Task2(void *pvParameters) {
    while (1) {
        taskENTER_CRITICAL();
        counter--;
        taskEXIT_CRITICAL();
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

在这个修改后的例子中，每个任务在访问 `counter` 时都使用了 `taskENTER_CRITICAL()` 和 `taskEXIT_CRITICAL()` 来保护临界区。这样可以确保在 `counter` 进行加或减操作时不会被其他任务打断，从而避免数据竞争。



## 13.互斥锁Mutex、自旋锁Spin

当加锁失败时，互斥锁用「线程切换」来应对，自旋锁则用「忙等待」来应对

互斥锁：Mutex，独占锁，谁上锁谁有权释放，申请上锁失败后阻塞，不能在中断中调用

自旋锁：Spinlock：申请上锁失败后，一直判断是否上锁成功，消耗CPU资源，可在中断中调用

**注：互斥锁有优先级继承，信号量没有。**

## 14.死锁和递归

死锁会发生在以下情况下：
1. **非递归锁**：如果任务已经持有某个锁，递归调用函数时再次获取同一个锁，则会导致死锁，因为该任务会无限期等待自己释放该锁，而自己已经被阻塞在等待锁释放的状态。
   
2. **锁的顺序不当**：如果在递归调用过程中，不同的锁按照不同的顺序被获取，可能导致死锁。

**递归锁的解决方案**

1. **递归锁（可重入锁）**：使用递归锁，它允许同一个任务多次获取同一个锁，而不会被阻塞。每次锁被获取，内部计数器增加；每次锁被释放，计数器减少，只有计数器为零时，锁才会真正被释放。
   
2. **避免在递归中使用锁**

**示例代码**

下面是一个示例，展示如何在递归函数中使用递归锁（可重入锁）来避免死锁：

```c
typedef struct {
    SemaphoreHandle_t mutex;  // 用于实际锁操作的FreeRTOS互斥信号量
    TaskHandle_t owner;       // 当前持有锁的任务的句柄
    UBaseType_t count;        // 当前任务持有锁的次数（递归锁的计数器）
} RecursiveLock_t;

void RecursiveLock_Init(RecursiveLock_t *lock) {
    lock->mutex = xSemaphoreCreateMutex();  // 创建一个互斥信号量
    lock->owner = NULL;                     // 初始化锁的拥有者为空
    lock->count = 0;                        // 初始化计数器为0
}

void RecursiveLock_Lock(RecursiveLock_t *lock) {
    TaskHandle_t currentTask = xTaskGetCurrentTaskHandle();  // 获取当前任务的句柄
    if (lock->owner == currentTask) {
        // 如果当前任务已经拥有该锁，则增加计数器
        lock->count++;
    } else {
        // 如果当前任务没有该锁，则尝试获取锁
        xSemaphoreTake(lock->mutex, portMAX_DELAY);  // 等待获取互斥信号量
        lock->owner = currentTask;                   // 设置当前任务为锁的拥有者
        lock->count = 1;                             // 初始化计数器为1
    }
}

void RecursiveLock_Unlock(RecursiveLock_t *lock) {
    TaskHandle_t currentTask = xTaskGetCurrentTaskHandle();  // 获取当前任务的句柄

    if (lock->owner == currentTask) {
        // 如果当前任务是锁的拥有者，则减少计数器
        if (--lock->count == 0) {
            // 如果计数器减为0，则释放锁
            lock->owner = NULL;                    // 重置锁的拥有者
            xSemaphoreGive(lock->mutex);           // 释放互斥信号量
        }
    }
}

RecursiveLock_t lock;  // 定义一个全局递归锁

void RecursiveFunction(int n) {
    RecursiveLock_Lock(&lock);  // 锁定资源
    // 递归结束条件
    if (n <= 0) {
        RecursiveLock_Unlock(&lock);  // 释放资源
        return;
    }
    // 递归调用
    RecursiveFunction(n - 1);
    RecursiveLock_Unlock(&lock);  // 释放资源
}
```



## 15.临界区与锁的对比

互斥锁与临界区的作用非常相似，但互斥锁（mutex）是可以命名的，也就是说它可以跨越进程使用。所以创建互斥锁需要的资源更多，所以如果只为了在进程内部使用的话使用临界区会带来速度上的优势并能够减少资源占用量。因为互斥锁是跨进程的互斥锁一旦被创建，就可以通过名字打开它。

临界区是一种轻量级的同步机制，与互斥和事件这些内核同步对象相比，临界区是用户态下的对象，即只能在同一进程中实现线程互斥。因无需在用户态和核心态之间切换，所以工作效率比较互斥来说要高很多。

|        | 使用场景             | 操作权限           |
| ------ | -------------------- | ------------------ |
| 临界区 | 一个进程下不同线程间 | 用户态，轻量级，快 |
| 互斥锁 | 进程间或线程间       | 内核态，切换，慢   |



## 16.同步互斥锁在消息队列如何应用

**互斥**：

互斥是通过某种锁机制（如互斥锁、信号量等）实现的，它确保在任何给定时刻，只有一个线程或进程可以操作消息队列。

1. **加锁**：任务操作消息队列时，首先尝试获得与队列关联的锁。如果锁已被其他线程占用，该线程将等待直到锁变为可用状态。
2. **执行操作**：一旦获得锁，线程就可以安全地执行其操作。
3. **释放锁**：操作完成后，线程释放锁。

**同步**：

确保生产者不会在队列满时尝试添加消息，消费者不会在队列空时尝试读取消息。

- **实际操作：**读取函数会有返回值，等于ture的时候才允许操作，否则挂起。

### **实际应用**

- FreeRTOS内部已经实现了线程安全机制，因此不需要额外的锁来保护对队列的访问。
- 具体来说，FreeRTOS的队列在内部使用了信号量（Semaphore）来保证多个任务（Task）对队列的并发访问是安全的。
- 在任务或者中断中调用消息队列传输的时候会进入临界区。
- 中断函数中有专门的ISR函数，不会执行阻塞操作，而且尝试直接写入，如果写入失败会返回false。



## 17.如何使消息队列性能更优（索引方式）

**使用索引来优化消息队列的传输效率，而不是直接传输大量数据。通过这种方式，减少了在消息队列中的数据传输量，同时提高了系统的整体性能。**

**传统方法：**

```
css复制代码消息队列
[ 数据块1 ][ 数据块2 ][ 数据块3 ] ...
```

- 每次传输大量数据，内存占用和传输时间较长。

**使用索引的方法：**

```
css复制代码消息队列
[ 索引1 ][ 索引2 ][ 索引3 ] ...

内存池
[ 数据块1 ][ 数据块2 ][ 数据块3 ] ...
```

- 消息队列中仅传输索引，内存池中存储实际数据。

**实现步骤**

1. **预分配内存块**：在系统初始化时，分配一定数量的固定大小的内存块。这些内存块用于存储实际的数据。

2. **空闲队列**：维护一个空闲内存块的队列。当需要发送数据时，从空闲队列中取出一个内存块。

3. **填充数据**：将数据填充到取出的内存块中。

4. **索引入队**：将内存块的索引（或指针）放入消息队列中。

5. **消费数据**：接收任务从消息队列中取出索引，通过索引找到对应的内存块，处理其中的数据。

6. **释放内存块**：处理完数据后，将内存块归还到空闲队列中。

### 示例代码

下面是一个使用 FreeRTOS 的示例代码，演示如何通过索引来优化消息队列的数据传输：

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include <stdio.h>

#define NUM_BLOCKS 10  // 内存块数量
#define BLOCK_SIZE sizeof(SensorData)  // 每个内存块的大小

// 传感器数据结构
typedef struct {
    float temperature;  // 温度
    float humidity;     // 湿度
    uint32_t timestamp; // 时间戳
} SensorData;

// 内存块结构
typedef struct {
    SensorData data;  // 传感器数据
} MemoryBlock;

MemoryBlock memoryPool[NUM_BLOCKS];  // 内存池数组
QueueHandle_t freeQueue;  // 空闲内存块队列
QueueHandle_t readyQueue; // 准备就绪内存块队列

// 初始化内存池
void initMemoryPool() {
    freeQueue = xQueueCreate(NUM_BLOCKS, sizeof(int));  // 创建空闲队列
    readyQueue = xQueueCreate(NUM_BLOCKS, sizeof(int)); // 创建就绪队列

    // 将所有内存块索引添加到空闲队列中
    for (int i = 0; i < NUM_BLOCKS; i++) {
        xQueueSend(freeQueue, &i, 0);
    }
}

// 传感器任务
void sensorTask(void *pvParameters) {
    int blockIndex;
    while (1) {
        // 从空闲队列中获取一个内存块索引
        if (xQueueReceive(freeQueue, &blockIndex, portMAX_DELAY) == pdPASS) {
            // 填充内存块中的传感器数据
            memoryPool[blockIndex].data.temperature = 25.0;  // 示例温度数据
            memoryPool[blockIndex].data.humidity = 60.0;     // 示例湿度数据
            memoryPool[blockIndex].data.timestamp = xTaskGetTickCount();  // 当前时间戳

            // 将内存块索引放入准备就绪队列
            xQueueSend(readyQueue, &blockIndex, portMAX_DELAY);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));  // 模拟传感器读取间隔
    }
}

// 数据处理任务
void processingTask(void *pvParameters) {
    int blockIndex;
    while (1) {
        // 从准备就绪队列中获取一个内存块索引
        if (xQueueReceive(readyQueue, &blockIndex, portMAX_DELAY) == pdPASS) {
            // 处理内存块中的传感器数据
            SensorData *data = &memoryPool[blockIndex].data;
            printf("Temperature: %.2f, Humidity: %.2f, Timestamp: %lu\n",
                   data->temperature, data->humidity, data->timestamp);

            // 将内存块索引归还到空闲队列
            xQueueSend(freeQueue, &blockIndex, portMAX_DELAY);
        }
    }
}

int main(void) {
    // 初始化内存池
    initMemoryPool();

    // 创建传感器任务
    xTaskCreate(sensorTask, "SensorTask", configMINIMAL_STACK_SIZE, NULL, 1, NULL);
    // 创建数据处理任务
    xTaskCreate(processingTask, "ProcessingTask", configMINIMAL_STACK_SIZE, NULL, 1, NULL);

    // 启动调度器
    vTaskStartScheduler();
    for (;;);
}

```

### 消息队列如何变化

**初始状态**

- `freeQueue`：`[0, 1, 2]`
- `readyQueue`：`[]`

**第一次传感器任务执行**

- `freeQueue`：`[1, 2]`
- `readyQueue`：`[0]`

**第一次数据处理任务执行**

- `freeQueue`：`[1, 2, 0]`
- `readyQueue`：`[]`

**第二次传感器任务执行**

- `freeQueue`：`[2, 0]`
- `readyQueue`：`[1]`

**第二次数据处理任务执行**

- `freeQueue`：`[2, 0, 1]`

- `readyQueue`：`[]`

  

## 18.STM32如果跑飞在异常中，怎么处理和定位问题？

https://www.cnblogs.com/yanxiaodong/p/13793274.html



## 19.如果一个系统内有一个高频的（20KHz）任务需要进行调度，应该怎么去设计实现？

***1.\**** ***\*确定任务优先级\****

\- **高频任务优先级**：高频任务通常应该有较高的优先级，以确保它能够按时调度执行。然而，优先级过高可能会导致低优先级任务饿死，特别是如果高频任务执行时间较长。

\- **优先级分配**：为系统中的所有任务分配合理的优先级，确保重要的任务（如紧急的错误处理）仍然能够及时执行。

***2.\**** ***\*设计任务执行时间\****

\- **执行时间短**：确保高频任务执行时间尽可能短，这样它才不会占用太多CPU时间，影响到其他任务。

\- **时间确定性**：任务的执行时间应该是确定的，避免在任务中调用可能导致不确定延迟的函数，如那些依赖外部资源的函数。

***3.\**** ***\*使用定时器或中断\****

\- **硬件定时器**：考虑使用硬件定时器来触发高频任务的执行。这样可以减少操作系统的负担，特别是在非常高的频率下。

\- **中断服务例程（ISR）**：如果任务对时间的要求非常严格，可以考虑将其实现为中断服务例程。但请注意，ISR中应避免执行长时间操作，并且只做最必要的处理。

***4.\**** ***\*使用信号量或事件组同步\****

\- 如果高频任务需要与其他任务交互，考虑使用信号量或事件组来进行同步。确保同步机制的使用不会导致任务被不必要地阻塞。

***5.\**** ***\*测试和验证\****

\- **性能测试**：使用FreeRTOS提供的工具和方法（如运行时间统计）来测试系统的实时性能，确保高频任务不会导致资源竞争或任务饥饿。

\- **优化**：根据测试结果进行必要的优化，可能包括调整任务优先级、优化任务代码，或改变任务调度策略。

***6.\**** ***\*实现示例\****

在FreeRTOS中，你可以使用`xTimerCreate`和`xTimerStart`创建和启动一个硬件定时器，或者使用`vTaskDelayUntil()`函数来创建一个周期性执行的任务。





## 20.FreeRTOS和Linux区别

最大的区别在于实时性，RTOS实时性好

| **特性**                 | **FreeRTOS**                                                 | **Linux**                                                    |
| ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **设计目标和应用场景**   | 开源的实时操作系统（RTOS），适用于资源受限的嵌入式系统，如工业控制、物联网设备、汽车电子等。 | 通用开源操作系统，适用于个人电脑、服务器、移动设备和嵌入式系统等多种计算环境，功能全面，支持广泛的硬件设备。 |
| **实时性**               | 提供确定性的任务调度，保证任务在严格定义的时间内完成，适合需要快速响应外部事件的应用。 | 标准Linux内核不是实时操作系统，提供良好的平均性能，但不保证确定性的响应时间。实时Linux变种（如PREEMPT_RT）可以提供更好的实时性能，但仍不及FreeRTOS。 |
| **资源需求**             | 内核小巧，几千字节内存即可运行，非常适合资源受限的环境。     | 资源需求较高，优化后的嵌入式Linux版本也需要至少数十兆字节的内存和更多的存储空间。 |
| **用户接口和开发复杂度** | 提供简洁的API管理任务、中断、同步机制等，适合直接在硬件上运行的应用程序开发。 | 提供丰富的用户界面和应用程序接口，支持图形界面、网络通信、文件系统等复杂功能。开发人员可使用多种编程语言和工具进行开发。 |
| **社区和生态系统**       | 具有活跃的社区和一些第三方库，但生态系统相对较小。           | 拥有庞大的开发者社区和丰富的软件生态系统，包括数以万计的应用程序和库，以及广泛的硬件支持。 |



### 最大的区别的实时性

***\*在实时性、中断处理和应用场景这三个方面，FreeRTOS和Linux表现出了显著的差异\****，这些差异直接影响了它们各自最适合的应用类型。

| **特性**     | **FreeRTOS**                                                 | **Linux**                                                    |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **实时性**   | 作为一个实时操作系统（RTOS），提供确定性的响应时间，保证系统在指定时间内响应外部事件。适用于需要快速和可预测响应的应用，如工业自动化和汽车电子系统。 | 标准Linux内核不是实时操作系统，调度器注重吞吐量和平均响应时间，不保证任务的最大延迟。实时Linux（如PREEMPT_RT）提高了实时性能，但仍不及专门设计的RTOS（如FreeRTOS）。 |
| **中断处理** | 中断处理设计为尽可能简短和快速。提供机制最小化中断服务例程（ISR）的执行时间，如允许从ISR中直接发送信号到任务或使用半任务（Half Task）处理。这保证了系统的实时性能。 | 中断处理相对较重，需处理更多上下文和系统状态。尽管进行了优化以快速处理中断，但在高负载或复杂系统中，中断响应时间可能不如RTOS。对于需要高优先级实时任务的系统，这可能成为问题。 |



### 中断造成的实时性差异

***\*Linux是软中断，rtos的中断是由nvic模块实现，中断是实时的，会立即响应或者不响应。Linux响应有延时\****

**RTOS中的中断**：

- 在RTOS中，中断通常由硬件直接管理，由嵌套向量中断控制器**（NVIC）**模块实现。NVIC负责管理和优先排序硬件中断，确保对**高优先级中断的快速响应**。

- RTOS设计以实时性为核心，这意味着系统能够保证在指定的、严格的时间限制内响应外部事件。因此，当中断发生时，RTOS能够确保几乎立即响应，或者基于预定义的优先级规则不响应。这种行为对于需要快速且一致响应外部事件的应用至关重要。


**Linux中的中断和软中断**：

- Linux操作系统区分硬中断（Hardware Interrupts）和软中断（Softirqs）/任务延迟（Tasklets）等机制。硬中断由硬件直接触发，而软中断是一种机制，用于在中断上下文之外处理中断相关的工作，这可以提高系统的整体性能和可扩展性。

- 软中断在Linux中用于分担一些不能在硬中断处理程序中执行的处理工作，比如说数据包处理等。这是因为硬中断处理程序需要尽可能快地执行并返回，以避免阻塞其他中断。**软中断可以被延迟执行**，这意味着它们的响应时间可能比直接的硬中断处理稍有延迟。


**响应延时的理解：**

- 当提到“Linux响应有延时”，主要是相对于RTOS直接和几乎立即处理硬中断的能力而言。Linux的软中断机制虽然提高了系统的灵活性和处理能力，但在面对需要极快响应的实时任务时，可能无法像RTOS那样提供最低延迟的保证。

- 这并不意味着Linux无法处理高速的或者实时的任务，但它的设计优先考虑的是灵活性和通用性，而非最严格意义上的实时响应。实时Linux变种（如使用PREEMPT_RT补丁的Linux）通过修改内核调度器和锁机制等方式，努力缩短响应时间，提高实时性。






## 21.Freertos内核中的驱动隔离

实现驱动隔离的主要目的是为了提高代码的模块性和可维护性，同时减少上层应用与硬件之间的直接依赖。

驱动隔离通常意味着创建一个抽象层，使应用代码与硬件操作解耦。

### 如何在STM32使用FreeRTOS实现驱动隔离

1. **驱动抽象层（HAL）**：
   - STM32通过其硬件抽象层（HAL）库提供了一个很好的起点，这些库封装了对硬件的直接访问，如GPIO, ADC, UART等。
   - 创建自定义的驱动抽象函数或接口，这些接口函数封装HAL函数，为应用层提供统一的调用接口。

2. **设备驱动接口**：
   - 定义设备驱动结构体，包含指向功能函数的指针（如初始化、读、写、关闭等）。
   - 应用层通过调用这些结构体中的函数指针来操作硬件，而无需关心具体的硬件细节。

3. **中间件层**：
   - 可以在HAL和应用层之间实现一个中间件层，这层处理更复杂的逻辑，如设备的状态管理、错误处理等。
   - 中间件层同样提供API，这些API基于设备驱动层的功能，向上提供更高层的服务。

4. **任务和信号量**：
   - 在FreeRTOS中，利用任务（Tasks）来隔离不同功能模块，每个任务处理特定的逻辑。
   - 使用信号量（Semaphores）或互斥锁（Mutexes）来管理对共享资源的访问，确保数据访问的线程安全。

5. **消息队列**：
   - 使用消息队列（Queues）来在任务之间传递数据，减少直接的任务间交互，可以通过队列发送消息或命令，从而驱动硬件操作。

6. **事件组和中断**：
   - 利用事件组来处理多个任务或中断之间的事件同步。
   - 在中断服务例程（ISR）中，尽量减少执行时间和复杂操作，使用中断来通知任务处理具体事件。

**示例代码概念**

假设我们需要为STM32中的一个UART接口写一个驱动，我们可以按照下面的步骤进行：

```c
// UART驱动接口
typedef struct {
    void (*init)(uint32_t baud_rate);
    void (*transmit)(const uint8_t* buffer, size_t size);
    void (*receive)(uint8_t* buffer, size_t size);
} UART_DriverInterface;

// 实现该接口
void UART_Init(uint32_t baud_rate) {}
void UART_Transmit(const uint8_t* buffer, size_t size)}
void UART_Receive(uint8_t* buffer, size_t size) {}

// 创建一个驱动结构体实例
UART_DriverInterface uart_driver = {
    .init = UART_Init,
    .transmit = UART_Transmit,
    .receive = UART_Receive
};

// 应用层调用
void app_function() {
    uart_driver.init(9600);
    uart_driver.transmit("Hello", 5);
}
```

通过这样的结构，应用代码与底层硬件操作解耦，便于维护和可扩展性。



### 在FreeRTOS上设计一个驱动框架

在FreeRTOS上设计一个驱动框架，以便更好地解耦上层应用和底层硬件驱动，可以借鉴Linux和RT-Thread中的驱动设计思路。以下是详细的设计步骤和思路：

**1. 驱动框架设计原则**

- **抽象硬件层（HAL）**：利用STM32 HAL库提供的硬件抽象层，使驱动程序可以直接调用HAL库来与硬件进行交互。
- **标准化接口**：定义统一的接口（如open、read、write、ioctl），使得上层应用可以通过这些接口来操作驱动，而不需要关心底层硬件的具体实现。
- **模块化设计**：每个驱动模块独立，实现特定硬件的操作，以便于维护和扩展。
- **线程安全**：确保驱动在多任务环境中是线程安全的，可以通过信号量、互斥锁等机制来实现。

**2. 驱动框架结构**

- **驱动管理层**：负责驱动的注册、注销和查找。
- **驱动接口层**：定义统一的驱动操作接口，如open、read、write、ioctl等。
- **驱动实现层**：每个具体的驱动实现，如UART驱动、I2C驱动等。

**3. 具体实现步骤**

**3.1 驱动接口定义**

首先定义驱动的通用接口，这些接口包括初始化、打开、读取、写入和控制等操作。

```c
typedef struct {
    int (*init)(void);
    int (*open)(void);
    int (*read)(char *buffer, int size);
    int (*write)(const char *buffer, int size);
    int (*ioctl)(int cmd, void *arg);
} driver_ops_t;

typedef struct {
    const char *name;
    driver_ops_t *ops;
} driver_t;
```

**3.2 驱动管理层**

实现一个驱动管理器，用于注册和查找驱动。

```c
#define MAX_DRIVERS 10

static driver_t *drivers[MAX_DRIVERS];
static int driver_count = 0;

int register_driver(driver_t *drv) {
    if (driver_count < MAX_DRIVERS) {
        drivers[driver_count++] = drv;
        return 0;
    }
    return -1;
}

driver_t* get_driver(const char *name) {
    for (int i = 0; i < driver_count; i++) {
        if (strcmp(drivers[i]->name, name) == 0) {
            return drivers[i];
        }
    }
    return NULL;
}
```

**3.3 驱动实现层**

每个具体的驱动实现，比如UART驱动，可以这样实现：

```c
#include "stm32f4xx_hal.h"

static int uart_init(void) {
    // UART初始化代码
    return 0;
}

static int uart_open(void) {
    // 打开UART
    return 0;
}

static int uart_read(char *buffer, int size) {
    // 从UART读取数据
    return HAL_UART_Receive(&huart1, (uint8_t *)buffer, size, HAL_MAX_DELAY);
}

static int uart_write(const char *buffer, int size) {
    // 向UART写入数据
    return HAL_UART_Transmit(&huart1, (uint8_t *)buffer, size, HAL_MAX_DELAY);
}

static int uart_ioctl(int cmd, void *arg) {
    // UART控制操作
    return 0;
}

driver_ops_t uart_ops = {
    .init = uart_init,
    .open = uart_open,
    .read = uart_read,
    .write = uart_write,
    .ioctl = uart_ioctl,
};

driver_t uart_driver = {
    .name = "uart1",
    .ops = &uart_ops,
};
```

在系统初始化时注册驱动：

```c
void system_init(void) {
    register_driver(&uart_driver);
}
```

**3.4 上层应用使用驱动**

上层应用通过统一接口使用驱动，而不需要关心具体实现。

```c
void app_main(void) {
    driver_t *uart = get_driver("uart1");
    if (uart && uart->ops->open()) {
        char buffer[100];
        uart->ops->read(buffer, sizeof(buffer));
        // 处理读取的数据
    }
}
```



## 22.如何设计任务

依据任务对响应的敏感性、执行时长（RTOS抢占式，会导致饥饿）

串口接收中断等任务优先级最高

电机PID计算以及控制需要固定控制周期，优先级较高

看门狗，按键处理中等、

最低的APP层的心跳和信息显示任务

**根据任务的控制频率和运行时间**（举例：视觉任务，算三角函数超时，一个三角函数6us 一个exp函数15us左右）



## 23.FreeRTOS的核心机制

实时操作系统（RTOS）的核心是其调度机制和任务管理。以下是RTOS最重要的几个核心概念和机制：

**1. 任务调度**

- **优先级调度**：高优先级任务优先运行。
- **时间片轮转**：为每个任务分配一个固定的时间片，轮流执行。
- **抢占式调度**：高优先级任务可以抢占低优先级任务的CPU时间。

**2. 任务管理**

RTOS提供了任务**创建、删除、挂起、恢复**等管理功能。

**3. 中断管理**

RTOS需要高效地处理中断。**FROM_ISR**

**4. 同步和通信机制**

- **信号量**（Semaphore）：用于任务间的同步和互斥。
- **互斥锁**（Mutex）：防止多个任务同时访问共享资源。
- **消息队列**（Message Queue）：用于任务间传递数据。
- **事件标志组**（Event Flags）：用于任务间的事件通知。
- **邮件箱**（Mailbox）：用于发送和接收消息。

**5. 内存管理**

RTOS提供动态内存管理机制，包括内存分配和释放，确保系统能够高效地利用内存资源。

**6. 上下文切换**

上下文切换是RTOS切换任务时保存和恢复任务状态的机制。它包括保存当前任务的CPU寄存器、堆栈指针和其他状态，并恢复新任务的这些状态。



## 24.RTOS如何任务调度

1. FreeRTOS在任务调度中有两种策略：优先级抢占和时间片轮询。
2. 创建任务的时候会给不同的任务分配不同的优先级，优先级是存储在对应任务的TCB中。
3. RTOS任务调度的底层是依赖就绪列表和阻塞列表进行的。
4. 列表的每个元素对应不同优先级的链表，链表中的每个节点关联到了不同任务的TCB。
5. 当系统触发了任务调度的时候，一般是当前任务主动阻塞（`vtaskyeild`）或者`systick`触发`pendsv`中断。
6. 会先执行保存上下文的操作，PC、通用寄存器、堆栈指针PSP、链接寄存器LR、程序状态寄存器xPSR、浮点寄存器。
7. 把当前任务移到阻塞列表中。
8. 执行`vTaskSwitchContext`函数，一般会先检查一个任务优先级的位图，通过硬件加速，CLZ指令查找**前导0**（第一个1前0的个数），获取最高优先级链表。
9. 在当前链表中选取任务，关联到新任务的TCB，然后恢复新任务的上下文，最后执行新任务。





# STM32

## 1.STM32启动程序过程

###  Bootloader

1.依据boot引脚选择启动区域

| 引脚 | 启动方式   | 描述                                           |
| ---- | ---------- | ---------------------------------------------- |
| x 0  | 片内Flash  | 代码区启动，ICP下载（SWD、JTAG烧录）           |
| 0 1  | 系统存储器 | 内置ROM启动，ISP下载（出厂预置代码，UART烧录） |
| 1 1  | SRAM       | RAM启动，掉电丢失                              |

2.运行bootloader

![20200807100320959.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20200807100320959.png)

​	处理器会将各个寄存器的值初始化为默认值

2.1 硬件设置SP、PC，进入复位中断函数Rest_Hander()

- 从0x0800 0000读取数据赋值给**栈指针**SP(MSP)，设置为栈顶指针0x2000 0000+RAM_Size

- 从0x0800 0004读取**复位中断函数地址数据赋值给PC**（指向Reset_Handler中断服务函数）


```c
Reset_Handler:
    LDR R0, =SystemInit  // 加载 SystemInit 函数的地址到 R0 寄存器
    BLX R0               // 跳转到 SystemInit 函数
    LDR R0, =__main      // 加载 __main 函数的地址到 R0 寄存器
    BX R0                // 跳转到 __main 函数
```

2.2 设置系统时钟，进入SystemInit()

- 设置RCC寄存器各位（**配置系统时钟**）

- 设置**中断向量表偏移地址**


```c
#ifdef VECT_TAB_SRAM
  SCB->VTOR = SRAM_BASE | VECT_TAB_OFFSET; /* Vector Table Relocation in Internal SRAM. */
#else
  SCB->VTOR = FLASH_BASE | VECT_TAB_OFFSET; /* Vector Table Relocation in Internal FLASH. */
#endif 
```

2.3 软件设置PC，跳转到__main（系统初始化函数）

```c
LDR R0,=__main
BX R0
```

- 拷贝Flash中的数据（data段包含已初始化的全局和静态变量）进入SRAM（哈弗体系结构决定了：数据与代码分开存储，flash断电不丢数据）
- 清零bss段（包含未初始化的全局和静态变量）

​		![0ea95a362db5457185191faf18069262.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/0ea95a362db5457185191faf18069262.png)

3 跳转到main()

```assembly
 BL main
```

![v2-1224644e63357ad886348dd630d9bce7_720w.webp](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/v2-1224644e63357ad886348dd630d9bce7_720w.webp)

![image-20230714215157086.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230714215157086.png)



### 自己实现OTA

可以在应用程序中实现OTA升级，而不需要修改原来的Bootloader。在新固件写入到Flash中的备用区域后，可以通过代码跳转到新固件。以下是详细步骤：

**1. 确定存储布局**

假设你的存储布局如下：
- **应用程序区域**：0x08000000 - 0x0807FFFF（512KB）
- **新固件区域**：0x08080000 - 0x080FFFFF（512KB）

**2. 应用程序中的OTA接收和写入逻辑**

应用程序通过无线通信接口接收新固件并写入Flash备用区域。更新完成后，跳转到新固件。

**示例代码**

```c
#include "stm32f4xx_hal.h"

#define NEW_FIRMWARE_START_ADDRESS 0x08080000

void SystemClock_Config(void);
void Wireless_Init(void);
bool ReceiveData(uint8_t *data);
void ReceiveAndFlashNewFirmware(void);
void JumpToApplication(uint32_t address);

int main(void) {
    HAL_Init();
    SystemClock_Config();
    Wireless_Init();
    
    while (1) {
        // 检查是否有新的固件需要更新
        if (/* 检测到需要更新 */) {
            ReceiveAndFlashNewFirmware();
            JumpToApplication(NEW_FIRMWARE_START_ADDRESS);
        }
    }
}

void SystemClock_Config(void) {
    // 配置系统时钟
}

void Wireless_Init(void) {
    // 初始化无线通信接口，如Wi-Fi、BLE等
}

void ReceiveAndFlashNewFirmware(void) {
    uint8_t data;
    uint32_t address = NEW_FIRMWARE_START_ADDRESS;
    
    HAL_FLASH_Unlock();
    
    FLASH_EraseInitTypeDef EraseInitStruct;
    uint32_t PageError;
    EraseInitStruct.TypeErase = FLASH_TYPEERASE_SECTORS;
    EraseInitStruct.VoltageRange = FLASH_VOLTAGE_RANGE_3;
    EraseInitStruct.Sector = FLASH_SECTOR_8; // 选择正确的扇区
    EraseInitStruct.NbSectors = 8; // 擦除的扇区数量
    
    if (HAL_FLASHEx_Erase(&EraseInitStruct, &PageError) != HAL_OK) {
        return;
    }
    
    while (ReceiveData(&data)) {
        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_BYTE, address, data) != HAL_OK) {
            return;
        }
        address++;
    }
    
    HAL_FLASH_Lock();
}

bool ReceiveData(uint8_t *data) {
    // 实现具体的接收数据逻辑，通过无线接口接收
    return true;
}

void JumpToApplication(uint32_t address) {
    void (*appResetHandler)(void) = (void (*)(void))(*((uint32_t *)(address + 4)));
    
    __disable_irq();
    SCB->VTOR = address;
    __set_MSP(*(volatile uint32_t *)address);
    appResetHandler();
}
```

### **新固件配置**

在实现OTA更新时，新固件的某些方面需要特别注意，以确保固件能够正确执行和跳转。以下是一些关键点和需要注意的事项：

**示例：链接脚本（.ld 文件）**

假设新固件的起始地址为 `0x08080000`，链接脚本的示例如下：

```ld
MEMORY
{
  FLASH (rx)      : ORIGIN = 0x08080000, LENGTH = 512K
  RAM (xrw)       : ORIGIN = 0x20000000, LENGTH = 128K
}
```

**示例：启动文件（.S 文件）**

需要确保向量表和启动代码能正确配置。

OTA更新过程中，会往flash中的一个固定地址写入新固件的起始地址。

在.s文件中自定义Reset_Handler函数，会先读取这个新固件的地址，在初始化完成之后使其跳转到新固件的地址。

**设置向量表偏移**

当新固件启动时，Bootloader应当设置正确的向量表偏移，以确保新固件的中断向量表能够正常工作。这通常在Bootloader的跳转代码中完成



## 2.编译过程

### 编译是干嘛的

编译是将高级编程语言（如 C、C++、Java 等）编写的源代码转换为计算机可以执行的机器代码（或中间代码、字节码）的过程。

### GCC编译

![image-20221130195604365.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221130195604365.png)

预处理：展开宏定义，文件嵌套、删除注释

编译：转换为汇编（检查语法不检查逻辑）

汇编：转换为机器码

链接：符号表查找与填充地址，库的链接，将汇编文件中函数的临时0地址进行填充，将每个符号定义与一个内存位置相关联起来

### STM32编译后程序大小与存放位置

1）Code：代码段，存放程序的代码部分；

2）RO-data：(Read Only )只读数据段，存放程序中定义的常量；

3）RW-data：(Read Write)读写数据段，存放初始化为非 0 值的全局变量；

4）ZI-data： (Zero Init) 数据段，存放未初始化的全局变量及初始化为 0 的变量；

```c
Total RO Size (Code + RO Data) 53668 ( 52.41kB)
Total RW Size (RW Data + ZI Data) 2728 ( 2.66kB)
Total ROM Size (Code + RO Data + RW Data) 53780 ( 52.52kB)
```

1）RO Size 包含了 Code 及 RO-data，表示程序占用 Flash 空间的大小；

2）RW Size 包含了 RW-data 及 ZI-data，表示运行时占用的 RAM 的大小；

3）ROM Size 包含了 Code、RO-data 以及 RW-data，表示烧写程序所占用的 Flash 空间的大小；

程序运行之前，需要有文件实体被烧录到 STM32 的 Flash 中，一般是 bin 或者 hex 文件，该被烧录文件称为可执行映像文件。如下图左边部分所示，是可执行映像文件烧录到 STM32 后的内存分布，它包含 RO 段和 RW 段两个部分：其中 RO 段中保存了 Code、RO-data 的数据，RW 段保存了 RW-data 的数据，由于 ZI-data 都是 0，所以未包含在映像文件中。

STM32 在上电启动之后默认从 Flash 启动，启动之后会将 RW 段中的 RW-data（初始化的全局变量）搬运到 RAM 中，但不会搬运 RO 段，即 CPU 的执行代码从 Flash 中读取，另外根据编译器给出的 ZI 地址和大小分配出 ZI 段，并将这块 RAM 区域清零。

![03Memory_distribution.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/03Memory_distribution.png)



编译过程：.c中的变量不分配地址（.o中函数、变量地址为0），链接时依据link file规则分配

链接：将各个.o中的相同段进行合并（.text、.data、.bss），并找到所有符号的引用与定义的位置



## 3.调试工具

keil+serialpolt+cubemx

segger的systemview可以查看freertos任务运行状态和时间

ozone可以查看变量和曲线



## 4.TIM定时器的中断方式

**定时器中断方式**

1. **更新中断**：
   
   - 当定时器的**计数器溢出**（即从最大值回到0）时，产生更新事件，触发更新中断。
   
2. **捕获/比较中断**：
   
   - 当定时器的捕获/比较寄存器**与计数器值匹配**时，产生捕获/比较事件，触发捕获/比较中断。
   
3. **触发中断**：
   
   - 当定时器触发**输入信号**（例如外部触发信号）到来时，产生触发事件，触发触发中断。
   



## 5.将flash中的代码放到sram中运行

1. **链接脚本（.ld）定义RAM段**：
   
    - **定义一个新的段** `.ramcode` 放置在RAM中，但**初始内容在Flash中**。
    - 使用 `AT> FLASH` **指定初始内容在Flash中的存储位置**。
    - 在.ld文件定义的**符号**_eramcode等会**在链接过程中被解析**，然后被.s文件获取。
    - `__attribute__((section(".ramcode")))` 告诉编译器将指定的函数放置在 `.ramcode` 段中。**具体的地址由链接脚本确定**。
    
    ```ld
    .ramcode : {
      _sramcode = .;  /* RAM代码段起始地址 */
      *(.ramcode*)    /* 代码段放置在此 */
      _eramcode = .;  /* RAM代码段结束地址 */
    } > RAM AT> FLASH
    ```
    
2. **启动代码复制段**：
    - 在 `Reset_Handler` 中，添加逻辑，将 `.ramcode` 段**从Flash复制到RAM中**。
    - 在代码段中获取.ld定义的**地址符号**，然后像.data段一样复制。

    ```assembly
    .extern _sidata
    .extern _sdata
    .extern _edata
    .extern _sirambegin
    .extern _sramcode
    .extern _eramcode
    
    Reset_Handler:
        /* 设置初始堆栈指针 */
        ldr   sp, =_estack
    
        /* 复制数据段初始化数据从Flash到RAM */
        ldr   r0, =_sidata
        ldr   r1, =_sdata
        ldr   r2, =_edata
    1:  cmp   r1, r2
        ittt  lt
        ldrlt r3, [r0], #4
        strlt r3, [r1], #4
        blt   1b
    
        /* 复制代码段从Flash到RAM */
        ldr   r0, =_sirambegin
        ldr   r1, =_sramcode
        ldr   r2, =_eramcode
    3:  cmp   r1, r2
        ittt  lt
        ldrlt r3, [r0], #4
        strlt r3, [r1], #4
        blt   3b
    ```

**3. 声明和使用SRAM中的函数**

`__attribute__((section(".ramcode")))` 是 GCC 编译器的一个扩展属性，用于将函数或变量放置在指定的内存段中。

```c
void my_sram_function(void) __attribute__((section(".ramcode")));
//__attribute__((section(".ramcode"))) 告诉编译器将 my_sram_function 放置在名为 .ramcode 的段中。
void my_sram_function(void) {
    // 这里是需要在SRAM中运行的代码
}
```



## 6.中断时M4内核发生了什么

1. **中断优先级检测**：
   NVIC检测到一个有效的中断请求，确定该中断是否具备更**高优先级**并且当前未被屏蔽。
2. **保存当前上下文**
4. **设置中断向量地址**：
   NVIC根据中断向量表查找ISR的入口地址，并将其加载到PC寄存器中。
5. **切换处理器状态**：
   - **调整程序状态寄存器（xPSR）**：将中断优先级级别更新到当前PSR中，以反映当前正在处理中断。
   - **切换堆栈指针**：根据处理器的配置（主堆栈指针MSP或进程堆栈指针PSP），切换到适当的堆栈指针。通常，中断处理使用主堆栈指针（MSP）。
6. **进入中断服务例程（ISR）**：
   PC指向ISR的入口地址，处理器开始执行中断处理程序。



# 内存管理

## 1.RTOS内存管理

**heap_1~5中除了heap_3分配在堆上，其余算法在.bss段开辟静态空间进行管理。没有内存池，可以自己实现。**

```c
// 定义内存堆的大小
#define configTOTAL_HEAP_SIZE (8 * 1024) // 8KB

// 全局变量 "uc_heap" 的定义
static uint8_t ucHeap[configTOTAL_HEAP_SIZE];
uint8_t *ucHeap = ucHeap;
```

[FreeRTOS笔记（六）：五种内存管理详解_CodeDog_wang的博客-CSDN博客](https://blog.csdn.net/weixin_43952192/article/details/108189300)

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

- 使用best fit算法来分配内存
- 合并相邻的空闲内存块

![856ee0739f2c46798c2c3dc3c76ff4c8.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/856ee0739f2c46798c2c3dc3c76ff4c8.png)

5. **heap_5**

在heap_4的基础上，可以从多个独立的内存空间分配内存。

### heap4

[FreeRTOS系列-- heap_4.c内存管理分析_为成功找方法的博客-CSDN博客](https://blog.csdn.net/yuanlin725/article/details/115087718)

1. **内存块合并**：
   Heap4支持相邻空闲内存块的合并，这有助于减少内存碎片，提高内存利用率。
2. **最佳适配**：
   Heap4使用最佳适配（best-fit）算法来选择最适合的空闲内存块进行分配。它在所有空闲块中找到一个大小最接近且能满足请求的块，这有助于减少内存碎片。

**Heap4的工作原理**

1. **初始化**：
   在FreeRTOS启动时，Heap4会初始化内存管理区域。将整个**可用内存区域**标记为一个大的**空闲块**，并将其添加到**空闲块链表**中。

2. **内存分配**：
   当应用程序请求内存分配时，Heap4会**遍历空闲块链表**，找到一个大小最接近且能满足请求的空闲块。如果找到合适的块，Heap4会将该块**分割成已分配块和剩余空闲块，然后返回已分配块的指针**。

3. **内存释放**：
   当应用程序释放内存时，Heap4会将该内存块标记为空闲，并尝试**将其与相邻的空闲块合并，形成一个更大的空闲块**。然后，Heap4会将合并后的**空闲块添加到空闲块链表**中。



## 2.mpu

**MPU**（Memory Protection Unit）是一种**硬件设备**，用于增强嵌入式系统的安全性和稳定性，通过管理每个程序对内存的访问权限。它的主要功能是防止软件错误对系统操作产生不良影响，以及隔离不同程序之间的内存访问，保护系统免受恶意软件攻击。

**MPU：**通过MPU对存储器的某些区域进行属性设置，设置其对特权级/用户级开放，可读可写/只读/只写、禁止访问、全访问、支持/禁止CACHE、缓冲等等的属性，通过MPU管理存储器，不至于某块内存被非法访问、数据破坏、CACHE等等。



## 3.mmu

**简述处理器在读内存的过程中，CPU 核、cache、MMU 如何协同工作?画出 CPU 核、 cache、MMU 、内存之间的关系示意图。**
**MMU的作用：**现代操作系统采用虚拟内存管理，这需要MMU(内存管理单元)的支持。MMU就是负责**虚拟地址**(virtual address)转化成**物理地址**。

**用MMU的：**`cortex-A`  windowsMacOs、Linux、Android

**不用MMU的：**`cortex-M`  FreeRTOS、VxWorks、Ucos

**MMU工作过程：**如果 CPU 启用了 MMU，CPU内核发出的地址将被 MMU截获,这时候从 CPU到 MMU的地址称为虚拟地址，而 MMU将这个 VA 翻译成为 PA发到 CPU 芯片的外部地址引脚上，也就是将 VA 映射到 PA中。

![image-20240701182606182.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240701182606182.png)

**注：TLB是一种cache**

## 4.cache

高速     中等速度   低速

CPU <------> Cache <-----> RAM

Cache，就是一种缓存机制，它位于CPU和DDR RAM之间，为CPU和DDR之间的读写提供一段内存缓冲区。cache读写速度要比DDR快不少。例如CPU要执行DDR里的指令，可以一次性的读一块区域的指令到cache里，下次就可以直接从cache里获取指令，而不用反复的去访问速度较慢的DDR。又例如，CPU要写一块数据到DDR里，它可以将数据快速地写到cache里，然后手动执行一条刷新cache的指令就可以将这片数据都更新到DDR里，或者干脆就不刷新，待cache到合适的时候，自己再将内容flush到DDR里。总之一句话，**cache的存在意义就是拉近CPU和DDR直接的性能差异，提高整个系统性能。**

Cache分为I-Cache（指令缓存）与D-Cache（数据缓存），使用LRU策略

![20210528111327990.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20210528111327990.png)

cache是多级的，在一个系统中你可能会看到L1、L2、L3, 当然越靠近core就越小，也是越昂贵。

CPU接收到指令后，它会最先向CPU中的一级缓存（L1 Cache）去寻找相关的数据，然一级缓存是与CPU同频运行的，但是由于容量较小，所以不可能每次都**缓存命中**。这时CPU会继续向下一级的二级缓存（L2 Cache）寻找，同样的道理，当所需要的数据在二级缓存中也没有的话，会继续转向L3 Cache、内存(主存)和硬盘.

![20210528111327990 - 副本.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20210528111327990%20-%20%E5%89%AF%E6%9C%AC.png)

### 不能使用cache的情况

1. CPU读取外设的内存数据，如果外设的数据本身会变，如网卡接收到外部数据，那么CPU如果连续2次读外设的操作相差时间很短，而且访问的是同样的地址，上次的内存数据还存在于cache当中，那么CPU第二次读取的可能还是第一次缓存在cache里数据。
2. CPU往外设写数据，如向串口控制器的内存空间写数据，如果CPU第1次写的数据还存在于cache当中，第2次又往同样的地址写数据，CPU可能就只更新了一下cache，由cache输出到串口的只有第2次的内容，第1次写的数据就丢失了。
3. 在嵌入式开发环境中，经常需要在PC端使用调试工具来通过直接查看内存的方式以确定某些事件的发生，如果定义一个全局变量来记录中断计数或者task循环次数等，这个变量如果定义为cache的，你会发现有时候系统明明是正常运行的，但是这个全局变量很长时间都不动一下。其实它的累加效果在cache里，因为没有人引用该变量，而长时间不会flush到DDR里
4. 考虑双cpu的运行环境(不是双核)。cpu1和cpu2共享一块ddr，它们都能访问,这块共享内存用于处理器之间的通信。cpu1在写完数据到后立刻给cpu2一个中断信号，通知cpu2去读这块内存，如果用cache的方法，cpu1可能把更新的内容只写到cache里，还没有被换出到ddr里，cpu2就已经跑去读，那么读到的并不是期望的数据。

![image-20230607151630997.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230607151630997.png)



### 为何启动时关闭Cache

在嵌入式系统和某些应用程序中，启动时关闭指令缓存（Instruction Cache）和数据缓存（Data Cache）是一种常见的做法。以下是一些原因：

1. 避免缓存冲突：在启动阶段，代码和数据通常是从外部存储器（如闪存）加载到内部存储器（如RAM）中。由于这些加载过程往往涉及重复的读写操作，启动时关闭缓存可以防止缓存中的“旧”数据对加载过程产生冲突，确保正确加载并执行新的代码和数据。
2. 简化启动过程：在关闭缓存的情况下，处理器将直接从内存中读取指令和数据，而不依赖于缓存。这样可以避免额外的缓存管理开销，并简化启动代码的编写和调试过程。
3. 确保数据的一致性：某些应用程序要求数据在内存和外部设备之间保持一致。在关闭缓存的情况下，每次访问数据都将直接从内存取，确内存中的数据始终与外部设备保持一致，关闭存并不适用于所有应用场景，并且可能会对性能产生负面影响。在实际应用中，应根据具体的系统需求和性能要求来决定是否关闭缓存。



### 存储器层次结构与分类

![20210528110828244.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20210528110828244.png)





4. 被替换。常见的替换策略包括最近最少使用**（LRU）**策略、随机替换和最不频繁使用（LFU）等。

**缓存的性能优化**

缓存的设计和优化对整个系统的性能有着显著的影响。设计者会考虑多种因素：

- **缓存的大小**：更大的缓存可以存储更多数据，减少缓存未命中的几率，但成本更高且可能增加访问延迟。
- **关联性**：缓存可以是直接映射、组相联或全相联。关联性越高，缓存命中率通常越高，但管理复杂性和成本也越大。
- **写策略**：包括写回（Write Back）和写通（Write Through）。写回策略中，数据仅在必要时更新到主内存；写通策略中，数据同时写入缓存和主内存。

通过这些方法，缓存有效地减少了CPU和主内存之间的速度差异，优化了计算机的运行效率。

在STM32F7微控制器中，开启Cache（包括指令缓存和数据缓存）是通过编程配置相关的系统寄存器来实现的。这通常在系统的初始化阶段进行，确保从启动开始就能够提升性能。以下是如何在STM32F7系列中开启Cache的基本步骤：

### 在stm32H7开启缓存cache

使用CMSIS函数来启用I-Cache和D-Cache。

```c
/* 使能 I-Cache */
SCB_EnableICache();

/* 使能 D-Cache */
SCB_EnableDCache();
```



## 5.堆和栈的区别

栈的动态分配主要是由编译器分配，由编译器自动释放；

堆只有动态分配用通过 `pvPortMalloc` 和 `vPortFree` 手动管理实现，由程序员手动释放

|          | 栈                                                     | 堆                                                           |
| -------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| 申请方式 | 系统分配与回收（栈内存分配运算内置于处理器的指令集）； | 程序员申请与释放                                             |
| 方向     | 高地址—》低地址；                                      | 低地址—》高地址                                              |
| 碎片问题 | 无碎片FIFO；                                           | 存在内外碎片                                                 |
| 存放内容 | 函数返回地址、局部变量的值；                           | 用户定义                                                     |
| 分配方式 | 栈的动态分配主要是由编译器分配，由编译器自动释放；     | 堆只有动态分配用通过 `pvPortMalloc` 和 `vPortFree` 手动管理实现，由程序员手动释放 |
| 内存位置 | 位于芯片的 SRAM                                        | 位于芯片的 SRAM                                              |



## 6.Flash 、SRAM

|      | Flash                                | SRAM                                                         |
| ---- | ------------------------------------ | ------------------------------------------------------------ |
| 用途 | 存储程序代码、存储常量数据           | 存储运行时数据（局部变量、全局变量、堆栈（Stack）和动态内存分配（Heap））、缓冲区 |
| 特点 | 掉电保存、读写速度慢、可擦写，1024KB | 掉电丢失、读写速度快、192KB                                  |

在典型的 STM32 系统中，内存分布大致如下：

```diff
+------------------------+
|  .text (程序代码)      |
+------------------------+
|  .data (已初始化数据)  |
+------------------------+
|  .bss (未初始化数据)   |
+------------------------+
|  堆 (Heap)             |
+------------------------+
|  栈 (Stack)            |
+------------------------+
|  其他内存区域          |
+------------------------+
```



## 7.任务栈爆炸

**常见原因**

1. **任务栈分配不足**：
   - 每个任务在创建时都会分配一定的栈空间。如果任务执行过程中使用的栈超过了分配的大小，就会导致栈溢出。
2. **递归调用**：
   - 递归调用可能导致栈深度迅速增加，特别是没有退出条件或退出条件不充分的递归。
5. **嵌套中断**：
   - 中断服务程序（ISR）如果占用过多栈空间，也可能导致栈溢出，尤其是嵌套中断的情况。

### **定位问题**

1. **启用栈检查**：
   
   - FreeRTOS 提供了几个选项来检测栈溢出，可以在 `FreeRTOSConfig.h` 文件中配置：
     ```c
     #define configCHECK_FOR_STACK_OVERFLOW 1
     ```
   - 方案1：在调度时检查栈指针是否越界（任务保存有栈顶和栈大小信息，每次切换时检查栈指针是否越界）
   
     - 优点：检测较快
     - 缺点：对于任务运行时溢出，而切换前又恢复正常的情况无法检测
   
     方案2：在调度时检查栈末尾的16个字节是否发生改变（创建任务时初始化为特定字符，每次切换时判断是否被改写）
   
     - 优点：可检出几乎所有溢出
     - 缺点：检测较慢
   
2. **查看任务栈高水位线**：
   - 在调试过程中，可以使用 `uxTaskGetStackHighWaterMark()` 函数查看每个任务剩余的最小栈空间。
     ```c
     UBaseType_t uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);
     ```

**解决问题**

1. **增大任务栈大小**：
   
   - 在创建任务时，适当增加任务的栈大小：
     ```c
     xTaskCreate(TaskFunction, "TaskName", configMINIMAL_STACK_SIZE + extra_stack_size, NULL, tskIDLE_PRIORITY, NULL);
     ```
   
2. **优化代码**：
   - 减少递归深度，或改用迭代方式。
   - 避免在栈上分配大数组或大变量，可以将其改为全局变量或动态分配在堆上。

3. **简化中断服务程序**：
   
   - 确保 ISR 短小精悍，将复杂处理移到任务上下文中。
   





# 通信、算法

## 1.rs232、485、uart、ttl的关系

***\*RS232、TTL和RS485\****都是串行通信接口标准，它们与UART（通用异步收发传输器）有一定的联系但又有重要的区别。**都是三根线。**

\- **RS232**和**TTL**都可以看作是UART信号的不同物理实现，一个用于较远距离通信，一个用于近距离或板间通信。

\- **RS485**是一种差分信号标准，适用于长距离和多设备网络通信。



## 2.CAN的CRC校验

***\*CAN（控制器局域网）协议中的CRC（循环冗余校验\****）是一种用于检测传输过程中帧错误的机制。每个CAN帧都包含一个CRC字段，该字段是根据帧的其他部分（起始位、帧ID、控制位、数据长度代码、数据字段等）计算出来的。接收方会对接收到的帧执行相同的CRC计算，并将计算结果与接收到的CRC字段进行比较，以验证数据的完整性。

***\*### 实际应用中的情况\****

在实际应用中，手动进行CRC校验通常是不必要的。***\*多数微控制器的CAN控制器和相关的硬件驱动库已经实现了CAN协议的所有细节，包括CRC校验。当CAN控制器接收到一个帧时，它会自动计算和校验CRC，只有在CRC校验通过的情况下，接收到的帧才会被认为是有效的，并通过软件接口传递给应用程序。\****

 

## 3.STM32DMA数据注意事项

当外部设备需要与主存储器进行数据交换时，需要通过中央处理器（CPU）作为中介来完成数据传输操作。然而，在大量数据传输的情况下，这样的方式会造成CPU过多地参与数据传输，降低了整体性能。

CPU将外设数据搬运到内存的顺序：

1. 外设设置状态寄存器置位
2. CPU读取外设数据寄存器到CPU通用寄存器
3. CPU将通用寄存器数据写入内存

**DMA**：CPU不介入情况下，将数据在外设与内存中传递。**DMA会节约总线资源吗（不能，他只是节约了CPU）**

![image-20230706174634517.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230706174634517.png)

### DMA配置

1. 配置DMA控制器：设置DMA通道、数据传输方向（外设到存储器或存储器到外设）、传输模式（单次传输、循环传输等）、数据宽度、传输计数等参数
2. 分配内存：如果是外设到存储器的数据传输，需要分配一块足够大小的缓冲区
3. 配置DMA通道：将外设和DMA通道连接起来，通常需要配置外设的DMA请求触发方式和DMA通道的优先级等参数。
4. 触发DMA传输：启动数据的传输。DMA控制器将自动执行数据的传输，而不需要CPU的干预。

### **实际应用**

- 分析性能瓶颈在哪，是数据频率还是数据量过大

- 数据频率：双DMA BUF

- 数据量：单个大 DMA BUF

  

 

## 4.电机传递函数

![image-20240630171737259.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240630171737259.png)

![image-20240630171737259.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240630171737259.png)

这两个方程是电机的拉普拉斯域（s域）中的传递函数，用于描述电机的动态行为。让我们逐一解释这两个方程：

***\*### 电流传递函数 \(I(s)\)\****

这个方程表示电机电流 \(I(s)\) 在s域中的表达式。它说明了电流是输入电压 \(U(s)\) 和由电机速度 \(\Omega(s)\) 产生的反电动势相减之后，经过电感 \(L\) 和电阻 \(R\) 的效果得到的。这里 \(K\) 是反电动势常数，\(Ls\) 表示电感对电流变化率的影响，而 \(R\) 表示电阻对电流的阻碍作用。

***\*### 速度传递函数 \(\Omega(s)\)\****

这个方程表示电机速度 \(\Omega(s)\) 在s域中的表达式。这里 \(K\) 是电磁转矩常数，与上面的 \(K\) 相同，它将电流 \(I(s)\) 转换成电磁转矩。分母中的 \(J\) 是转动惯量，代表电机转子质量的分布对其加速度的影响；\(b\) 是阻尼系数，代表了机械系统中的摩擦和阻力。

在闭环控制系统的框图中，这两个传递函数相互耦合。电流传递函数的输出 \(I(s)\) 经过转矩常数 \(K\) 的放大，成为速度传递函数的输入，而速度传递函数的输出 \(\Omega(s)\) 又通过 \(K\) 影响电流传递函数的输入。这个闭环系统说明了电机速度和电机电流之间的相互依赖关系，以及它们如何受到电机参数 \(L, R, J, b\) 和转矩常数 \(K\) 的影响。

这种分析在设计电机控制系统时非常重要，因为它帮助工程师理解如何通过调整控制输入来改变电机的速度和加速度。此外，这些方程也是设计PID（比例-积分-微分）控制器或其他类型控制器时的基础，使得电机能够达到期望的性能指标。

 

在物理电路中：

***\*- 电感 \( L \) 是电路元件，它对电流的变化产生阻力\****。当电流试图改变时，电感会产生一个阻止电流改变的电压，这是由于电磁感应产生的。在数学上，电感对电流的这种作用是通过微分方程 \( L \frac{di(t)}{dt} \) 来描述的，即电感值乘以电流随时间的变化率。

***\*- 转动惯量 \( J \) 是描述物体抵抗旋转速度变化的物理量\****。它在机械系统中的作用类似于电感在电路中的作用。当外部力矩试图改变物体的旋转速度时，转动惯量会阻碍这种变化。这在数学上通过方程 \( J \frac{d\omega(t)}{dt} \) 描述，即转动惯量乘以角速度随时间的变化率。

在控制系统中，当我们使用拉普拉斯变换将这些物理行为从时间域转换到s域时：

\- 电感的影响表示为 \( Ls \)，这里的 \( s \) 代表复频率变量，它在数学上对应于时间域的微分操作。

\- 转动惯量的影响表示为 \( Js \)，同样的 \( s \) 在这里代表时间导数。

总结起来，\( Ls \) 和 \( Js \) 在拉普拉斯变换中表示电感和转动惯量对系统动态行为的“抵抗效果”。它们不是在物理上直接抵抗某件事，而是在数学上描述了电流和角速度随时间变化的能力。在s域中，这种“抵抗”通过乘以 \( s \) 来体现。希望这样解释能更清晰地说明 \( s \) 在这些方程中的作用。

 

## 5.CAN的终端电阻

![image-20240702160721049.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20240702160721049.png)

1. **阻抗匹配：**CAN网络是基于双绞线传输的差分信号。为了最大限度地减少信号反射，提高信号质量，需要在CAN网络的两端分别添加终端电阻，以匹配网络的特性阻抗（通常为120欧姆）。如果没有适当的阻抗匹配，信号反射可能导致数据误差和通信干扰。
2. **提高信号完整性：**通过防止信号反射，终端电阻有助于保持数据的完整性，确保数据在整个网络中稳定、准确地传输。
4. **确保差分信号电压：**在信号显性状态期间，总线的寄生电容会被充电，而在恢复到隐性状态时，这些电容需要放电，加个中断电阻帮助放电。

***\*信号反射\****

信号反射是电信号在传输线（如同轴电缆、双绞线等）中遇到阻抗不连续时发生的现象。当电信号遇到这种阻抗不连续时，部分信号会被反射回源头，而非全部传输到目的地。这种反射会引起多种问题，如信号干扰、数据丢失或误差，尤其在高速通信中影响显著。

***\*阻抗匹配\****

阻抗匹配是指使信号源、传输线、和负载（接收端）之间的阻抗保持一致，以最大限度地减少或消除信号反射。传输线的特性阻抗是线材和其结构决定的固有属性，而不依赖于线路的长度。标准的CAN网络使用的双绞线特性阻抗为120欧姆。

> 小电阻大作用 https://zhuanlan.zhihu.com/p/26096996





## 6.IMU、四元数

**解算欧拉角过程：**

1. SPI读取六轴角度
2. 积分消除零偏（主要受地区g影响）、温度补偿消除温飘
3. 数据过低通滤波
4. Mahony计算四元数（通过角速度积分计算姿态，用加速度进行误差修正）
5. 四元数反解欧拉角

**问题：**

Mahony算法将加速度测量结果直接认为是实际重力加速度，无法分辨加速度计测量结果中除重力加速度外的运动加速度，因此运动加速度会严重破坏其姿态解算精度。

**解决办法：**

卡尔曼滤波器区分运动加速度和重力加速度。

**低通滤波需要注意截止频率：**

[陀螺仪数据处理(BMI088)-CSDN博客](https://blog.csdn.net/weixin_44080304/article/details/125065724)

先采用数据，通过FFT查看频谱图，确定高频噪声频率范围，根据采样频率和截止频率确定低通滤波参数。

**设计低通滤波器**

根据采样频率和截止频率计算滤波器系数

系数带入滤波器函数，我们使用的是IIR（二阶无限脉冲响应）滤波器。

### Mahony

互补滤波，用角速度积分计算姿态，用加速度补偿，先去把重力加速度算出来，和实际的加速度做一个PI的控制，输出一个变量叫bias，用这个bias去修正误差



## 7.KF

用于过滤高斯噪声（白噪声）

![watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L0NTRE5fWF9X,size_16,color_FFFFFF,t_70.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L0NTRE5fWF9X,size_16,color_FFFFFF,t_70.png)

![image-20221213120732933.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221213120732933.png)

**实际应用**

- 电机数据滤波，去除噪声
- 视觉数据预测，补帧

**通过k-1时刻的最优估计值预测k时刻的理论值，并根据k时刻的测量值，进行数据融合，得到k时刻的最优估计值**（线性离散时不变系统，误差正态分布）**通过不断更新卡尔曼增益来最小化估计值的方差，从而获得对系统状态的最优估计**

```c
x(k) = A · x(k-1) + B · u(k) + w(k)  // 预测方程：依据k-1时刻的状态，推算k时刻的状态
z(k) = H · x(k) + y(k)  // 观测方程

x(k) —— k时刻系统的状态
u(k) —— 控制量
w(k) —— 符合高斯分布的过程噪声，其协方差在下文中为Q
z(k) —— k时刻系统的观测值
y(k) —— 符合高斯分布的测量噪声，其协方差在下文中为R
A、B、H —— 系统参数，多输入多输出时为矩阵，单输入单输出时就是几个常数
```

在后面滤波器的方程中我们将不会再直接面对两个噪声w(k)和y(k)，而是用到他们的协方差Q和R。至此，**A、B、H、Q、R**这几个参数都由被观测的系统本身和测量过程中的噪声确定了。

```c
// 时间更新（预测）
x(k|k-1) = A · x(k-1|k-1) + B · u(k)  // 系统状态(x)
P(k|k-1) = A · P(k-1|k-1) · AT + Q  // 系统协方差(P)
K(k) = P(k|k-1) · HT · (H · P(k|k-1) · HT + R)-1  // 卡尔曼增益K(k)
// 测量更新（校正融合）
x(k|k) = x(k|k-1) + K(k) · (z(k) - H · x(k|k-1))  // 输出值（后验估计）x(k|k)
P(k|k) = (I - K(k) · H) · P(k|k-1)  // 更新误差协方差
```

实际使用：

```c
x  // 观测量初始值
P  // 系统协方差
K  // 卡尔曼增益，自动计算
Q  // 过程噪声的协方差，对初值不敏感，很快收敛
R  // 测量噪声的协方差，↑后平滑但是响应变差且收敛慢
while(新观测值)
{
    K = P / (P + R);  // 增益
    x = x + K * (新观测值 - x);  // 输出
    P = (1 - K) · P + Q;  // 更新
}

float Kalman_Filter(float data) {
	static float prevData = 0;
	static float p = 1;  // 估计协方差
	static float q = 1;  // 过程噪声协方差
	static float r = 5;  // 观测噪声协方差，控制响应速率
	static float kGain = 0;
	
	p += q;
	kGain = p / (p + r);		//计算卡尔曼增益
	data = prevData + (kGain * (data - prevData));		//计算本次滤波估计值
	p = (1 - kGain) * p;		//更新测量方差
	prevData = data;
	return data;
}
```



```c
//1. 结构体类型定义
typedef struct {
    float LastP;//上次估算协方差 初始化值为0.02
    float Now_P;//当前估算协方差 初始化值为0
    float out;//卡尔曼滤波器输出 初始化值为0
    float Kg;//卡尔曼增益 初始化值为0
    float Q;//过程噪声协方差 初始化值为0.001
    float R;//观测噪声协方差 初始化值为0.543
}KFP；//Kalman Filter parameter

//2. 以高度为例 定义卡尔曼结构体并初始化参数
KFP KFP_height={0.02,0,0,0,0.001,0.543};

/*卡尔曼滤波器
 *@param KFP *kfp 卡尔曼结构体参数
 *   float input 需要滤波的参数的测量值（即传感器的采集值）
 *@return 滤波后的参数（最优值）*/
//卡尔曼滤波器是一种最优滤波器，其核心思想是通过不断更新卡尔曼增益来最小化估计值的方差，从而获得对系统状态的最优估计
 float kalmanFilter(KFP *kfp,float input) {
     //系统协方差方程：k时刻系统估算协方差 = k-1时刻的系统协方差 + 过程噪声协方差
     kfp->Now_P = kfp->LastP + kfp->Q;
     //卡尔曼增益方程：卡尔曼增益 = k时刻系统估算协方差 / （k时刻系统估算协方差 + 观测噪声协方差）
     kfp->Kg = kfp->Now_P / (kfp->NOw_P + kfp->R);
     //更新最优值方程：k时刻状态变量的最优值 = 状态变量的预测值 + 卡尔曼增益 * （测量值 - 状态变量的预测值）
     kfp->out = kfp->out + kfp->Kg * (input -kfp->out);//因为这一次的预测值就是上一次的输出值
     //更新误差协方差方程: 本次的系统协方差付给 kfp->LastP 为下一次运算准备。
     kfp->LastP = (1-kfp->Kg) * kfp->Now_P;
     return kfp->out；
 }

//调用卡尔曼滤波器 实践
float height;
float kalman_height = 0;
kalman_height = kalmanFilter(&KFP_height, height);
```



## 8.弹道解算

**已知坐标和距离，求补偿角度**

竖直方向(z)：

$$
z = v_0tsinθ - \frac{1}{2}gt^2
$$

用二分法猜角度带入公式求Z，最后求得Z误差较小时退出。

以下是实现该方法的Python代码：

```python
def calculate_trajectory(v0, theta, x0, y0, xf, yf, g=9.81):
    R = xf - x0
    theta_rad = math.radians(theta)
    
    t_flight = R / (v0 * math.cos(theta_rad))
    y_final = y0 + v0 * t_flight * math.sin(theta_rad) - 0.5 * g * t_flight**2
    
    return y_final

def find_launch_angle(v0, x0, y0, xf, yf, g=9.81, tolerance=1e-6):
    low = 0
    high = 90
    while high - low > tolerance:
        mid = (low + high) / 2
        y_mid = calculate_trajectory(v0, mid, x0, y0, xf, yf, g)
        
        if y_mid > yf:
            high = mid
        else:
            low = mid
    
    return (low + high) / 2
```



问：为什么不让linux算

相机帧率，控制帧率，IMU帧率。下位机补帧，预测位置对应弹道解算也要变

问：可以把整套给上位机

希望有更多数据交互，让下位机有决策空间，如速度等数据。有一些coner case需要处理，比如我们相机是跟着云台P轴动的，对面机器人很远的时候弹道解算出来P轴抬的很高，视野里就会丢失目标。

## 9.怎么理解IIC

**I²C 总线的基本概念**

1. **双线通信**：
   - I²C 总线使用两条线进行通信：
     - **SDA**：数据线，负责在设备之间传输数据。
     - **SCL**：时钟线，由主设备生成，用于同步数据传输。
2. **主从架构**，**应答机制**：
   - I²C 总线采用主从架构，一个主设备（Master）可以控制一个或多个从设备（Slave）。
   - 谁生成时钟信号谁就是主设备，从设备根据主设备的指令进行响应。
   - 有一套完整的应答机制保证数据传输的准确性。
3. **设备地址**：
   - 每个从设备都有一个唯一的7位或10位地址，主设备通过地址选择具体的从设备进行通信。
4. **双向通信**：
   - 数据线（SDA）是双向的，可以在主设备和从设备之间传输数据。
   - 主设备可以写数据到从设备，也可以从从设备读取数据。

**I²C 总线的工作原理**

1. **启动和停止条件**：
   - **启动条件（Start Condition）**：当SCL高电平时，SDA从高电平变为低电平，表示通信的开始。
   - **停止条件（Stop Condition）**：当SCL高电平时，SDA从低电平变为高电平，表示通信的结束。

2. **数据传输**：
   - 数据以字节为单位传输，每个字节包含8位数据。
   - 每传输一个字节后，发送设备会释放SDA线，接收设备通过拉低SDA线发送一个确认位（ACK），表示成功接收数据。如果接收设备不拉低SDA线，则表示不确认（NACK）。

3. **读写操作**：
   - **写操作**：主设备发送从设备地址和写指令（最低位为0），然后发送数据字节。
   - **读操作**：主设备发送从设备地址和读指令（最低位为1），然后从从设备读取数据字节。

**I²C 总线的优点**

1. 节省引脚和线路
   
2. 简单易用
   
3. 多主设备支持

**I²C 总线的局限性**

1. 传输速率限制
2. 距离限制



## 10.iic如何分辨读和写

分辨读和写操作是通过在地址帧之后的一个读/写位（R/W bit）来实现的。这个 R/W 位决定了主机（Master）是要读取从机（Slave）的数据还是写数据到从机。

- **R/W 位是由主机发送的**：用于指示当前操作是读还是写。

  - **R/W 位为 0**：主机向从机写数据。
  - **R/W 位为 1**：主机从从机读数据。

- **从机根据 R/W 位的状态执行操作**：从机根据主机发送的 R/W 位决定是接收数据（写操作）还是发送数据（读操作）。

  
  
  

## 11.spi和iic的区别

| 特性         | SPI                                        | I²C                                                        |
| ------------ | ------------------------------------------ | ---------------------------------------------------------- |
| 通信方式     | 全双工（同时发送和接收）                   | 半双工（单方向发送或接收）                                 |
| 信号线       | 4 条（MOSI, MISO, SCK, SS/CS）             | 2 条（SDA, SCL）                                           |
| 最大数据速率 | 高达几十 MHz                               | 标准模式：100 kbps，快速模式：400 kbps，高速模式：3.4 Mbps |
| 主从设备     | 单主多从                                   | 多主多从                                                   |
| 设备选择方式 | 通过独立的片选线选择从设备                 | 通过设备地址选择从设备                                     |
| 复杂度       | 简单                                       | 较复杂                                                     |
| 硬件实现     | 简单，易于实现                             | 较复杂，需要处理地址和仲裁                                 |
| 典型应用     | 高速数据传输，短距离通信，如 SD 卡、显示屏 | 低速通信，需要地址管理，如 EEPROM、传感器                  |
| 总线拉低时间 | 无                                         | 有，影响速度                                               |

### **速度差异的原因**

| 特性               | SPI                              | I²C                                         |
| ------------------ | -------------------------------- | ------------------------------------------- |
| **信号驱动方式**   | 推挽驱动，可快速拉高拉低         | 开漏驱动 ，拉高时间取决于上拉电阻           |
| **信号线数量**     | 4 条（MOSI, MISO, SCK, SS/CS）   | 2 条（SDA, SCL）                            |
| **通信模式**       | 全双工、两条线同时通信           | 半双工、只有一条数据线                      |
| **设备选择方式**   | 独立的片选线 (CS)                | 通过设备地址 、增加时间                     |
| **协议开销**       | 低、没有复杂的握手信号和确认机制 | 高、包含地址帧、应答位（ACK/NACK）、读/写位 |
| **握手和仲裁机制** | 无                               | 有                                          |



## 12.SPI时钟不匹配

SPI是主从同步通信协议，时钟信号（CLK）由主设备生成并控制通信节奏，所有从设备都依赖该时钟信号同步数据传输。

**常见原因**

| **原因**           | **描述**                                                     |
| ------------------ | ------------------------------------------------------------ |
| **时钟配置不一致** | 主设备和从设备的时钟极性（CPOL）和时钟相位（CPHA）配置不一致会导致数据传输错误。 |
| **时钟频率不匹配** | 主设备的时钟频率过高，从设备无法及时处理，导致数据丢失或读取错误。 |
| **信号完整性问题** | 电气噪声、长电缆、差劲的布线等会引起时钟和数据信号的失真，导致同步问题。 |

**定位问题**

| **方法**              | **描述**                                                     |
| --------------------- | ------------------------------------------------------------ |
| **示波器/逻辑分析仪** | 使用示波器或逻辑分析仪检查时钟信号（SCLK）、主输出从输入（MOSI）、主输入从输出（MISO）和从设备选择（CS）信号的波形，确认时钟和数据是否正确。 |
| **配置检查**          | 检查主从设备的SPI配置，包括时钟极性（CPOL）、时钟相位（CPHA）、时钟频率等，确保一致。 |
| **软件调试**          | 增加调试日志，记录主从设备的初始化和数据传输过程，检查是否有错误配置或数据传输异常。 |

**解决方案**

| **方案**         | **描述**                                                     |
| ---------------- | ------------------------------------------------------------ |
| **统一配置**     | 确保主从设备的SPI配置参数一致，特别是时钟极性（CPOL）和时钟相位（CPHA）。 |
| **降低时钟频率** | 如果时钟频率过高，从设备无法响应，可以适当降低主设备的时钟频率。 |
| **改进电气设计** | 使用短且高质量的连接线，增加去耦电容，使用屏蔽线或差分信号传输，确保信号完整性。 |



## 13.旋转矩阵

如何将相机内的目标的四个点转换为实际的坐标点。

假设相机视角中的四个顶点坐标为：
- $$P1' = (100, 100) $$（零点左下角）
- $$P2' = (200, 150)$$
- $$P3' = (250, 250)$$
- $$P4' = (150, 200) $$

**步骤 1：计算方向向量和倾角**

选择一个方向向量（比如$$ (V1' = P2' - P1')$$：
$$ V1' = (200 - 100, 150 - 100) = (100, 50)  $$
计算方向向量的倾角：
$$  \theta' = \arctan2(50, 100) = \arctan2(1, 2) \approx 0.4636 \text{ 弧度} \approx 26.57^\circ  $$

**步骤 2：构建旋转矩阵**

根据计算的倾角 \(\theta'\)，构建旋转矩阵 \(R\)：
$$
R = \begin{pmatrix}
\cos(0.4636) & -\sin(0.4636) \\
\sin(0.4636) & \cos(0.4636)
\end{pmatrix} 
= \begin{pmatrix}
0.8944 & -0.4472 \\
0.4472 & 0.8944
\end{pmatrix}
$$
**步骤 3：应用旋转矩阵将点转换到相机坐标系**

对于长方体内的任意一点 \(P'' = (x'', y'')\)（相对于左下角点 \(P1'\) 的坐标），可以通过以下步骤计算其在相机坐标系中的坐标 \(P' = (x', y')\)。

假设我们选择点 \(P'' = (10, 20)\)：

1. 计算相对于左下角点的偏移量：
$$
\Delta P = \begin{pmatrix}
10 \\
20
\end{pmatrix} 
$$

2. 应用旋转矩阵 \(R\) 将偏移量转换到相机坐标系中：
$$
  
  \Delta P' = R \cdot \Delta P = \begin{pmatrix}
  0.8944 & -0.4472 \\
  0.4472 & 0.8944
  \end{pmatrix} \cdot \begin{pmatrix}
  10 \\
  20
  \end{pmatrix} 
$$

$$
  
  \Delta P' = \begin{pmatrix}
  0.8944 \cdot 10 + (-0.4472) \cdot 20 \\
  0.4472 \cdot 10 + 0.8944 \cdot 20
  \end{pmatrix} = \begin{pmatrix}
  8.944 - 8.944 \\
  4.472 + 17.888
  \end{pmatrix} = \begin{pmatrix}
  0 \\
  22.36
  \end{pmatrix}
$$

  

3. 将转换后的偏移量加上左下角点的坐标，得到在相机坐标系中的最终坐标：
$$
  P' = \Delta P' + P1' = \begin{pmatrix}
  0 \\
  22.36
  \end{pmatrix} + \begin{pmatrix}
  100 \\
  100
  \end{pmatrix} = \begin{pmatrix}
  100 \\
  122.36
  \end{pmatrix}
$$

因此，长方体内任意一点的坐标 \(P'' = (10, 20)\) 在相机坐标系中的最终坐标 \(P' = (100, 122.36)\)。



## 14.图像坐标怎么转换到世界坐标

图像坐标 -> 相机坐标 -> 机器人坐标（云台坐标）-> 世界坐标

**1. 图像坐标到相机坐标**

首先，需要使用相机的内参矩阵将图像坐标转换到相机坐标系。

$$ \begin{pmatrix} x_c \\ y_c \\ z_c \end{pmatrix} = K^{-1} \begin{pmatrix} u \\ v \\ 1 \end{pmatrix} $$

其中，\( K \) 是相机的内参矩阵，\( (u, v) \) 是图像坐标，\( (x_c, y_c, z_c) \) 是相机坐标系中的坐标。具体来说，内参矩阵 \( K \) 通常是这样的形式：

$$ K = \begin{pmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{pmatrix} $$

这里，\( f_x \) 和 \( f_y \) 是焦距，\( (c_x, c_y) \) 是图像中心。

**2. 相机坐标到云台坐标**

相机固定在云台上，通常会有一个固定的旋转和平移关系。这个关系可以通过外参矩阵表示。假设相机坐标系到云台坐标系的转换矩阵为 \( [R_t | t_t] \)，其中 \( R_t \) 是旋转矩阵，\( t_t \) 是平移向量。

$$ \begin{pmatrix} x_t \\ y_t \\ z_t \\ 1 \end{pmatrix} = \begin{pmatrix} R_t & t_t \\ 0 & 1 \end{pmatrix} \begin{pmatrix} x_c \\ y_c \\ z_c \\ 1 \end{pmatrix}  $$

**3. 云台坐标到世界坐标**

云台的IMU数据可以提供云台相对于世界坐标系的姿态（欧拉角、四元数等）。假设云台相对于世界坐标系的旋转矩阵为 \( R_w \)，平移向量为 \( t_w \)。

$$ \begin{pmatrix} x_w \\ y_w \\ z_w \\ 1 \end{pmatrix} = \begin{pmatrix} R_w & t_w \\ 0 & 1 \end{pmatrix} \begin{pmatrix} x_t \\ y_t \\ z_t \\ 1 \end{pmatrix} $$ 

**具体步骤**

假设已知图像坐标 \( (u, v) \)、相机内参矩阵 \( K \)、相机到云台的外参矩阵 \( [R_t | t_t] \)、云台的IMU数据提供的旋转矩阵 \( R_w \) 和平移向量 \( t_w \)，可以按以下步骤进行转换。

**1. 图像坐标到相机坐标**

```python
import numpy as np

# 相机内参矩阵
K = np.array([[f_x, 0, c_x],
              [0, f_y, c_y],
              [0, 0, 1]])

# 图像坐标
u, v = 100, 150  # 这是示例坐标

# 将图像坐标转换到相机坐标
uv1 = np.array([u, v, 1])
xyz_c = np.linalg.inv(K).dot(uv1)

# 假设一个深度值 z_c，通常需要深度传感器或其他信息提供深度
z_c = 1.0  # 示例深度值
xyz_c *= z_c
```

**2. 相机坐标到云台坐标**

```python
# 相机到云台的旋转矩阵和平移向量
R_t = np.eye(3)  # 示例，实际需要根据相机与云台的相对姿态
t_t = np.array([0, 0, 0])  # 示例，实际需要根据相机与云台的相对位置

# 构建相机到云台的转换矩阵
T_ct = np.hstack((R_t, t_t.reshape(3, 1)))
T_ct = np.vstack((T_ct, [0, 0, 0, 1]))

# 将相机坐标转换到云台坐标
xyz_c_h = np.append(xyz_c, 1)  # 齐次坐标
xyz_t_h = T_ct.dot(xyz_c_h)
xyz_t = xyz_t_h[:3]
```

**3. 云台坐标到世界坐标**

```python
# 云台的IMU数据提供的旋转矩阵和平移向量
R_w = np.eye(3)  # 示例，实际需要从IMU获取
t_w = np.array([0, 0, 0])  # 示例，实际需要从IMU获取

# 构建云台到世界的转换矩阵
T_tw = np.hstack((R_w, t_w.reshape(3, 1)))
T_tw = np.vstack((T_tw, [0, 0, 0, 1]))

# 将云台坐标转换到世界坐标
xyz_t_h = np.append(xyz_t, 1)  # 齐次坐标
xyz_w_h = T_tw.dot(xyz_t_h)
xyz_w = xyz_w_h[:3]
```



## 15.PID怎么调

[从不懂到会用！PID从理论到实践~_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1B54y1V7hp/?spm_id_from=333.337.search-card.all.click&vd_source=1d37ae9e25605e1121cee9187de16dab)

速度环负责快速控制动态响应，角度环负责慢速控制最终目标。

控制系统的输出为电流，通过电机系统的速度传递函数控制角速度。

**为什么要双环？**

1. **提高响应速度和稳定性**：
   - 这种内外环的结构能够有效提高系统的响应速度和稳定性。内环的快速响应有助于迅速抑制扰动，外环的慢速调整有助于保证系统的精确度。
2. **分离控制目标**：
   - 角度环和速度环的分离能够将复杂的控制问题分解为两个相对简单的控制任务。
   - 速度环负责快速控制动态响应，角度环负责慢速控制最终目标。
   - 通过分离控制目标，设计和调试PID参数变得更加简单和有效。

**采用串级PID的优势与原因**

**不同工况适应性：**对于不同的系统工况，由于电机实际输入是电流（直接控制转速），当电机负载不同时（原有PID参数用于平地行驶，现在爬坡行驶），电机系统模型也不同，采用同一套位置环PID算法较难获得稳定的电机电流输出信号，导致同一套参数的控制效果在其他工况变差。串级PID的引入，使得内环可以让电机速度更快地跟随。

**系统稳态要求：**若仅有位置环PID，达到指定位置时，由于没有对速度的限制，因此可能发生震荡。引入内环后速度也有PID控制器进行反馈，当位置较小时，内环的输入也会变小，从而约束稳态速度减小到0。

**限制速度：**对于内环而言，可以采用输出限幅的方式限制转速，从而避免了单位置环PID在偏差较大时电机速度过快。

### 如何评价PID系统好坏

1. **稳态误差：**
   - 确保系统在达到设定值后，误差尽可能小。
   - 通过调节比例（P）和积分（I）参数来减小稳态误差。

2. **上升时间：**
   - 指系统从初始值达到设定值一定比例（通常是90%）所需的时间。
   - 主要受比例（P）参数的影响。

3. **调节时间**：
   - 指系统进入并保持在目标值一定范围内所需的时间（例如±2%）。
   - 受比例（P）、积分（I）和微分（D）参数共同影响。

4. **超调量**：
   - 系统响应超过设定值的最大值。
   - 主要通过调节比例（P）和微分（D）参数来控制。

5. **稳定性**：
   - 系统在各种扰动下保持稳定，不产生持续振荡或发散。
   - 通过综合调节P、I、D参数来保证系统稳定性。

6. **响应速度和抑制扰动能力**：
   - 系统对设定值变化的响应速度及其抑制外部扰动的能力。

### 调整PID参数的方法

1. **初步设置**：
   - 关闭I和D，只调整P参数，直到系统达到临界振荡。
   - 找到**临界增益** 𝐾𝑢，继续增加kp，直到系统的输出开始持续振荡，且振荡幅度稳定不变。
   - 找到临界周期Pu，系统振荡的周期。
2. **设置初始PID参数**：
   - 根据Ziegler-Nichols**齐格勒－尼科尔斯**或其他经验公式设置初始PID参数。
3. **进行闭环测试**：
   - 对系统施加阶跃输入，观察响应曲线。
4. **参数微调**：
   - 根据响应曲线调整PID参数，重点关注稳态误差、上升时间、调节时间和超调量。
5. **频域验证**：
   - 进行频域分析，确保系统在频域内的性能满足要求。
6. **实际应用测试**：
   - 在实际应用环境中进一步验证和调整PID参数，确保系统在各种工作条件下稳定可靠。

| 控制器类型 | 比例增益 \( K_p \)    | 积分增益\( K_i \)                | 微分增益 \( K_d \)             |
| ---------- | --------------------- | -------------------------------- | ------------------------------ |
| P          | $$( K_p = 0.5K_u )$$  | -                                | -                              |
| PI         | $$( K_p = 0.45K_u )$$ | $$( K_i = \frac{K_pP_u}{1.2} )$$ | -                              |
| PID        | $$( K_p = 0.6K_u )$$  | $$( K_i = \frac{K_pP_u}{2} )$$   | $$( K_d = \frac{K_pP_u}{8} )$$ |



## 16.重力补偿

$$
M_g = m \cdot g \cdot r_g \cdot \sin(\theta)
$$

其中，\( r_g \) 是重心到P轴的垂直距离。随着P轴角度变化，**重力矩**也在变化。

重心位置不好测量，原本尝试过通过sw添加模型材质，自动求解模型重心，效果一般。

后来干脆直接让电机输出固定的扭矩，看在什么角度下刚好和重力矩抵消。用这个方法测量不同角度下的重力矩，然后拟合成一个函数。函数的输入是p轴角度，输出是角度对应的重力矩，最后的效果是没有闭环的情况下可以在任意角度停下。



## 17.FOC

1. FOC通过**Clarke变换和Park变换**将三相交流电流和电压转换为两相直流分量（d轴和q轴）。

2. 然后通过**PI调节器独立控制d轴电流和q轴电流**，从而实现对电机磁通和转矩的精确控制。

3. 提高电机的动态性能和运行效率，使其在各种转速和负载条件下保持平稳高效运行。

   

## 18.涡流传感器



# 基础、语法

## 1.为什么static修饰的变量在别的文件不可访问

根本原因是**链接过程中的符号解析规则**。`static`关键字通过限制符号的可见性范围至定义它的文件（编译单元），在根本上阻止了跨文件访问.

1. **编译阶段**：在编译阶段，编译器将 .c文件---->编译----->.o文件。在这个过程中，编译器会处理源代码中的`static`声明，并将这些`static`变量或函数标记为仅在当前源文件内部可见。这意味着这些符**号不会被导出到目标文件的符号表**中。
2. **链接阶段**：链接阶段是构建过程的第二步，链接器将所有的目标文件和库文件合并成最终的可执行文件。在这个过程中，链接器解析程序中的符号引用，将每个引用关联到它的定义上。如果一个符号被声明为`static`，**它的定义就不会出现在目标文件的全局符号表中，因此链接器无法在其他目标文件中找到它的引用**。

***\*链接错误的原因\****

**链接器在全局符号表中找不到这个符号**，因此无法解析引用，导致链接错误。

 

## 2.C中的栈和队列是怎么实现的

在C语言中，栈和队列这两种数据结构通常是通过数组或链表来实现的，因为C语言本身并不直接提供这些数据结构的支持。以下是栈和队列的基本概念以及它们在C语言中的典型实现方式：

***\*栈(Stack)\****

栈是一种**后进先出**的数据结构，常用操作包括push（添加元素到栈顶）、pop（从栈顶移除元素）和peek（查看栈顶元素）。

数组实现：

使用数组实现栈时，***\*通常会指定一个索引来表示栈顶的位置\****。初始化时，栈顶的索引可以设置为-1，表示栈为空。每次push操作，索引增加，并在新的索引位置存储元素；每次pop操作，返回当前索引位置的元素，并将索引减少。

链表实现：

使用链表实现栈时，可以将链表的头部作为栈顶。push操作就是在链表头部添加一个新节点，pop操作就是移除链表头部的节点。

***\*队列(Queue)\****

队列是一种先进先出的数据结构，常用操作包括enqueue（在队尾添加元素）、dequeue（从队头移除元素）和peek（查看队头元素）。

数组实现：

使用数组实现队列时，***\*需要两个索引来分别跟踪队头和队尾\****。当进行enqueue操作时，在队尾位置插入元素并更新队尾索引；进行dequeue操作时，返回队头元素并更新队头索引。为了高效利用空间，通常会实现循环队列。

链表实现：

使用链表实现队列时，需要保持对头节点和尾节点的引用。enqueue操作在链表尾部添加一个新节点，dequeue操作移除头部节点。

 

## 3.递归的实现原理

递归的基本思想是函数自己调用自己，每次调用都是在解决问题的一个更小的子集。为了理解递归的底层实现机制，我们需要从几个关键点来探讨：调用栈（Call Stack）、基线条件（Base Case）和递归步骤（Recursive Step）。

***\*调用栈（Call Stack）\****

- **后进先出。**在大多数编程语言中，函数调用会使用到一种名为“调用栈”的数据结构。每当一个函数被调用时，一个新的栈帧（Stack Frame）就会被创建并压入调用栈中。这个栈帧包含了函数的参数、局部变量以及其他函数调用相关的信息。
- 在递归过程中，每一次函数自身的调用都会在调用栈中创建一个新的栈帧，这些都是独立的，不会互相干扰。


***\*基线条件（Base Case）\****

- 也就是递归的终止条件。当满足这个条件时，函数开始逐层返回。没有基线条件的递归将会导致无限递归，最终耗尽调用栈空间，引发栈溢出错误。


***\*递归步骤（Recursive Step）\****

- 除了基线条件外，递归函数还需要定义一个或多个递归步骤。在每次递归调用时，问题的规模应该比上一次有所减小，直到达到基线条件。这一步是实现递归逻辑的核心。


***\*底层实现示例\****

考虑一个简单的递归函数示例：计算一个数字的阶乘（n!）。在这个例子中，n! 定义为 n * (n-1) * (n-2) * ... * 1。这个问题的基线条件是 n = 1（因为 1! = 1），递归步骤是 n! = n * (n-1)!。

```python
def factorial(n):
# 基线条件
if n == 1:
	return 1
# 递归步骤
else:
	return n * factorial(n - 1)
```

在上面的例子中，每次调用factorial时，都会在调用栈中添加一个新的栈帧，直到达到基线条件。之后，函数开始逐层返回，每层递归都利用返回的值计算上一层的结果，直到最初的调用返回最终结果。

 

## 4.栈在递归的时候的作用

***\*### 栈的基本概念\****

你可以将栈想象成一摞盘子：你只能在顶部添加（push）或移除（pop）盘子。栈在递归中的核心作用是保存每次递归调用的状态，以便在每层递归完成后能够正确地“倒回去”。

***\* 简化的例子\****

假设我们有一个递归函数，它打印出从1到给定数字n的所有数字。当我们调用这个函数，比如说`printNumbers(3)`，栈的使用情况如下：

1. **首次调用`printNumbers(3)`**: 调用信息被推入栈。
2. **递归调用`printNumbers(2)`**: 由于`printNumbers(3)`中调用了`printNumbers(2)`，`printNumbers(2)`的调用信息被推入栈，位于`printNumbers(3)`之上。
3. **递归调用`printNumbers(1)`**: 同样，`printNumbers(1)`的调用信息被推入栈，位于`printNumbers(2)`之上。

当`printNumbers(1)`达到基本情形并开始返回时，栈开始逐步弹出每个调用的信息，**先是`printNumbers(1)`，然后是`printNumbers(2)`，最后是`printNumbers(3)`**。这个过程确保了每个函数调用都能在执行完毕后正确返回到它被调用的地方。



##  5.手写Strcpy和strcmp

\- `strcmp`函数用于比较两个字符串。它逐个字符地比较两个字符串，直到发现不同的字符或遇到字符串的结束符`\0`。如果第一个字符串在字典顺序上小于第二个字符串，它返回一个负数；如果两个字符串相等，返回0；如果第一个字符串大于第二个字符串，它返回一个正数。

\- `strcpy`函数用于复制字符串。它将包含结束符`\0`的源字符串复制到目标字符串中。目标字符串必须足够大，能够存放源字符串的副本，包括结束符`\0`。

这两个函数的原型如下：

```c
int strcmp(const char *str1, const char *str2);

char *strcpy(char *dest, const char *src);
```

\- `strcmp`的返回值是整型，它根据比较的结果返回负数、0或正数。

\- `strcpy`的返回值是指向目标字符串（`dest`）的指针。

每个函数都有其特定的用途和返回类型，它们在处理字符串时互不替代。

复现`strcmp`函数可以通过比较两个字符串的每个字符来实现。`strcmp`函数用于比较两个字符串，并根据比较结果返回整数。具体地，如果第一个字符串小于第二个字符串，则返回负数；如果两个字符串相等，则返回0；如果第一个字符串大于第二个字符串，则返回正数。这里的“小于”和“大于”是基于字符的ASCII值来比较的。

 

***\*下面是一个手写`strcmp`函数的示例代码，使用C语言实现：\****

```c
#include <stdio.h>

// strcpy 函数的实现
char* strcpy(char* dest, const char* src) {
    char* saved = dest;
    while (*src) {
        *dest++ = *src++;
    }
    *dest = 0;  // 添加字符串结束符 '\0'
    return saved;
}

// 测试代码
int main() {
    char src[] = "Hello, World!";
    char dest[20];  // 确保有足够的空间
    strcpy(dest, src);
    printf("Copied string: %s\n", dest);
    return 0;
}
```

 

在这个实现中：

- **复制过程**：我们逐字符复制源字符串 `src` 到目标字符串 `dest`。
  
- **使用循环继续复制**：使用一个 `while` 循环，持续复制字符，直到遇到源字符串的结束符 `'\0'`。这意味着复制包括了源字符串的所有字符，但不包括终止符。

- **递增指针**：在每次循环中，`src` 和 `dest` 指针都递增，指向各自字符串的下一个字符。这样的操作保证了字符串的每个字符都能被正确复制到目标位置。

- **添加结束符**：在源字符串的所有字符复制完成后，在目标字符串的当前位置添加一个空字符（`'\0'`），作为字符串的结束符。这一步骤是必要的，因为在 C 语言中，字符串以 `\0` 结束。

- **返回复制的字符串**：函数返回保存的目标字符串的起始地址，这样调用者就可以直接使用返回的字符串地址进行进一步操作或输出。

这个实现简单直观，能够高效地完成字符串的复制任务。

 

***\*手写`strcpy`函数\****的关键是逐个字符地从源字符串复制到目标字符串，直到包括字符串结束符`'\0'`。下面是一个简单的`strcpy`函数的实现示例，使用C语言：

```c
#include <stdio.h>

// strcpy 函数的实现
char* strcpy(char* dest, const char* src) {
    char* saved = dest;
    while (*src) {
        *dest++ = *src++;
    }
    *dest = 0;  // 添加字符串结束符 '\0'
    return saved;
}

// 测试代码
int main() {
    char src[] = "Hello, World!";
    char dest[20];  // 确保有足够的空间
    strcpy(dest, src);
    printf("Copied string: %s\n", dest);
    return 0;
}
```

这个实现的步骤如下：

1. 定义`my_strcpy`函数，接受两个参数：`dest`（目标字符串的指针）和`src`（源字符串的指针）。
2. 在函数内部，首先保存目标字符串的起始地址到`ret`变量中，以便最后返回。
3. 使用一个`while`循环逐字符复制源字符串到目标字符串，直到遇到源字符串的结束符`'\0'`。在复制每个字符后，同时递增`src`和`dest`指针。
4. 循环结束后，手动在目标字符串末尾添加结束符`'\0'`。
5. 最后，返回目标字符串的起始地址。

这种实现方式简单直观，能够有效地完成字符串复制的任务。



## 6.两个float怎样比较相同

float的精度是保证至少**7位有效数字**是准确的。

在编程中比较两个浮点数是否相同时，直接使用 `==` 运算符通常是不可靠的。

**原因：**这是因为浮点数在计算机中以有限精度存储，许多看似相等的浮点数在实际存储时可能会有微小的差异。

**浮点数比较的原因和问题**

1. **有限精度**：
   - 浮点数在计算机中使用 IEEE 754 标准表示，这种表示方式导致某些十进制数在二进制中无法精确表示。
   - 算术运算（加、减、乘、除）在结果中引入的舍入误差也会影响浮点数的比较。

2. **舍入误差**：
   - 浮点运算可能产生舍入误差，即使是相同的运算在不同的硬件或编译器上执行，也可能产生微小的差异。

**方法**

比较它们的差值是否在一个很小的范围内（即误差范围内）。这个范围通常称为 `epsilon`。

**代码示例**

以下是一个使用 `epsilon` 的示例代码，用于比较两个浮点数是否近似相等：

```c
// 定义一个很小的误差范围
#define EPSILON 1e-6

int are_floats_equal(float a, float b) {
    return fabs(a - b) < EPSILON;
}
```



## 7.队列

C可以由链表实现

- 添加：添加头节点
- 移除：遍历到末节点



# Linux网络 

## 1.Socket概念和代码

**\*基本概念\***

***\*1. \*\*Socket\*\**\***：Socket是网络通信的端点，提供了两个应用程序之间通过网络进行数据交换的机制。在大多数操作系统中，Socket API可用于实现客户端和服务器之间的通信。

***\*2. \*\*Socket类型\*\**\***：

 \- **流式Socket（SOCK_STREAM）**：使用传输控制协议（TCP），提供面向连接、可靠的字节流服务。

 \- **数据报Socket（SOCK_DGRAM）**：使用用户数据报协议（UDP），提供无连接、不保证可靠性的数据包服务。

***\*3. \*\*IP地址和端口\*\**\***：IP地址用于标识网络上的设备，而端口用于标识设备上的特定应用程序。Socket通过IP地址和端口号的组合来确定数据的发送和接收端点。

**\ 简单的TCP服务器和客户端**

***\**\*服务器（Python示例）\*\*：\****

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(('localhost', 8080))

server_socket.listen()

print("Server is listening")

while True:

  client_socket, addr = server_socket.accept()

  print("Connection from", addr)

  client_socket.sendall(b'Hello, client')

  client_socket.close()

```

***\**\*客户端（Python示例）\*\*：\****

```python
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(('localhost', 8080))

message = client_socket.recv(1024)

print(message.decode())

client_socket.close()
```

***\*#### 步骤\****

1. **编写服务器代码**：服务器创建一个Socket，绑定到特定的IP和端口上，然后开始监听连接请求。当接收到请求时，它接受连接，发送一个消息，然后关闭连接。
2. **编写客户端代码**：客户端创建一个Socket，连接到服务器的IP和端口，接收来自服务器的消息，然后关闭连接。
3. **运行服务器和客户端**：首先运行服务器， 它将开始监听端口。然后运行客户端，它将连接到服务器，接收消息并打印出来。

 



## 2.TCP和UDP的区别

\- **连接导向 vs 无连接**：

- TCP是面向连接的协议，通信双方必须先建立连接才能交换数据。
- UDP是无连接的，发送数据之前不需要建立连接。

\- **可靠性**：

- TCP提供可靠的数据传输，确保数据按顺序到达，无重复、无丢失。
- UDP则不保证数据的可靠性，数据包可能丢失或顺序错乱。

\- **速度和效率**：

- TCP由于其确认机制和重传机制，通常比UDP慢。
- UDP由于缺少这些机制，处理速度更快，效率更高，但牺牲了可靠性。

\- **应用场景**：

- TCP适用于需要高可靠性的应用，如Web浏览、电子邮件、文件传输等。
- UDP适用于对实时性要求高的应用，如流媒体、在线游戏、VoIP等。

**\* `bind()`, `listen()`, `accept()`在服务器端的作用\***

- \- **`bind()`**：将Socket绑定到一个地址和端口上。在服务器开始监听客户端连接之前，必须指定它的IP地址和端口号。

- \- **`listen()`**：使服务器的Socket进入监听状态，等待客户端的连接请求。它还定义了请求队列的最大长度。

- \- **`accept()`**：当客户端尝试连接到服务器时，`accept()`函数接受连接请求。如果有多个连接请求，`accept()`会处理队列中的下一个连接请求。该函数返回一个新的Socket，专用于与请求的客户端通信。


***\*###什么是端口冲突，如何避免\****

端口冲突发生在两个应用程序尝试绑定到同一端口号时。为避免端口冲突，可以：

\- 使用操作系统提供的机制自动选择空闲端口。

\- 配置应用程序使用不同的端口号。

\- 对于已知的服务，遵循标准端口号，对于自定义的服务，选择高端口号范围内的端口。

***\*### 解释TCP三次握手和四次挥手过程\****

### \- **三次握手**

1. 客户端发送SYN包到服务器，并进入SYN_SEND状态。
2. 服务器收到SYN包，回复一个SYN+ACK包，进入SYN_RECV状态。
3. 客户端收到SYN+ACK包，发送一个ACK包给服务器，双方建立连接。

### \- **四次挥手**

1. 当通信一方完成数据发送任务，发送一个FIN包开始关闭连接。
2. 另一方收到FIN包后，发送ACK包确认，并将自己的连接置为半关闭状态，等待自己的数据发送完成。
3. 数据发送完毕后，也发送一个FIN包给对方。
4. 对方收到FIN包后，发送ACK包作为回应，完成连接关闭。

这些过程确保了TCP连接的可靠建立和终止，防止了数据丢失和连接状态的不确定性。

 

 

## 3.ros节点通信

在机器人操作系统（ROS）中，节点之间的通信主要通过以下几种方式实现，这些机制允许分布式的处理单元（节点）在复杂的机器人系统中协同工作。创建发布者/订阅者节点

1. **主题（Topics）**

\- **机制**：基于发布/订阅模型，节点可以发布消息到一个主题或订阅一个主题来接收消息。这种方式适用于不同节点之间的异步通信。

\- **用途**：适用于高频率的数据交换，例如，传感器数据流、状态更新等。

\- **特点**：提供了一种松耦合的通信方式，发送者（发布者）和接收者（订阅者）不需要知道对方的存在。

2. **服务（Services）**

\- **机制**：基于请求/响应模型，一个节点可以提供一个服务，其他节点可以通过发送请求来调用这个服务并得到响应。服务调用是同步的，调用方会阻塞直到收到响应。

\- **用途**：适用于那些需要即时响应的交互，如获取环境数据或者执行某个操作并需要确认结果。

\- **特点**：服务调用提供了一种更加紧密的双向通信方式。

3. **动作（Actions）**

\- **机制**：动作是建立在主题和服务之上的高级通信机制，适用于需要长时间运行的任务。动作客户端发送一个目标给动作服务器，并且能够接收到关于任务执行状态的反馈，以及最终的结果。

\- **用途**：适用于长时间运行的任务，如导航、移动等，同时需要周期性反馈执行状态。

\- **特点**：动作通信允许中断执行的任务，提供了一种灵活的交互方式。

4. **参数服务器（Parameter Server）**

\- **机制**：参数服务器提供了一个集中存储配置参数的机制，允许节点在运行时获取和设置参数值。虽然不是直接的通信方式，参数服务器却是节点间共享配置信息的有效手段。

\- **用途**：适用于存储和共享配置参数，如机器人的尺寸、摄像头参数等。

\- **特点**：提供了一种集中式的配置管理，简化了节点间配置信息的共享和更新。

 

 

## 4.ros节点有用到socket方式吗

ROS节点在底层通信时确实使用了Socket方式。

***\*### ROS底层通信机制：\****

\- **主题（Topics）**：主要通过TCP/IP Sockets实现，确保数据的可靠传输。在某些情况下，也可以配置为使用UDP协议（通过UDP的ROS协议，即UDPROS）来传输数据，尤其是在对实时性要求较高且可以容忍数据丢失的场景中。

\- **服务（Services）**：服务调用通常是基于同步的TCP/IP连接实现的，服务的请求和响应都是通过这个连接传输。

\- **动作（Actions）**：动作库在顶层使用了服务和主题的组合来实现长时间运行的任务，因此其底层通信也是基于TCP/IP Sockets。

***\*### 为什么使用Socket：\****

Socket通信允许ROS节点跨网络进行数据交换，这意味着ROS的分布式计算模型不仅限于单个物理机器，节点可以分布在不同的机器上，只要它们能够通过网络相互连接。这种设计极大地提升了ROS在复杂机器人系统中的灵活性和扩展性。

 

 

## 5.使用GDB

***\*### 编译代码以供GDB使用\****

为了使用GDB调试程序，你需要在编译时***\*带上`-g`选项\****，这样才能生成调试信息。

```shell
gcc -g program.c -o program
```

***\*### 启动GDB\****

启动GDB并加载你的程序：

```shell
gdb ./program
```

***\*### GDB基本命令\****

\- `run`：启动程序。你可以带参数运行，例如：`run arg1 arg2`。

\- `break`：在函数或行号设置断点，例如：`break main` 或 `break 24`。

\- `continue`：从当前位置继续执行程序，直到遇到下一个断点。

\- `next`：执行下一行代码，但不进入函数体内部。

\- `step`：执行下一行代码，如果有函数调用则进入函数。

\- `print`：打印变量的值，例如：`print x`。

\- `list`：列出源代码。给定函数名或行号时，可以列出特定部分的代码。

\- `quit`：退出GDB。

***\*### 使用示例\****

1. **设置断点**：你可以在程序的主函数设置一个断点。

```shell
 (gdb) break main
```

2. **运行程序**：然后运行你的程序。

```shell
 (gdb) run
```

3. **逐行执行**：程序会在断点处停下来，然后你可以逐行执行来检查程序的执行流程。

```shell
 (gdb) next
```

4. **查看变量**：在任何时刻，你都可以查看变量的值。

```shell
 (gdb) print variable_name
```

5. **继续执行**：如果你想继续执行到下一个断点，或者程序结束。

```shell
 (gdb) continue
```

6. **退出GDB**：

```shell
 (gdb) quit
```

 

## 6.MQTT

***\*MQTT\****是一种基于发布/订阅模式的轻量级消息传输协议，设计用于低带宽、高延迟或不可靠的网络环境。确实，MQTT是建立在TCP/IP协议之上的，这意味着它利用了TCP的连接特性，如可靠性、有序性和数据完整性保证，来进行消息的传输。

**MQTT和TCP的区别：**

***协议层次不同：TCP\****（Transmission Control Protocol）是一种传输层协议，负责在网络中的两个主机之间建立可靠的、有序的和错误检测的数据传输。而MQTT是一个应用层协议，它定义了消息的格式和规则，使得设备能够发布消息和订阅主题，进行有效的通信。

***用途和目标不同：\****TCP为多种应用层协议提供传输服务，如HTTP、FTP等，它本身并不关心传输的数据内容。相反，MQTT专门设计用于消息传输，特别是在物联网（IoT）场景中，提供了一种高效的方式来处理设备之间的通信，支持一对多的消息发布。

***功能和特性不同：\****MQTT在TCP的基础上提供了更多针对消息传输优化的功能，如保持活动（Keep Alive）机制、消息队列、主题过滤和三种不同的消息传递质量等级（QoS）。这些功能使得MQTT在网络条件不稳定或资源受限的环境中表现更加可靠。

***轻量级：\****相比直接使用TCP，MQTT设计为轻量级的，它的协议头非常小（最小仅2字节），这对于带宽有限的环境非常重要。



MQTT是基于TCP协议的一种应用层消息传输协议。它利用了TCP的可靠性和有序性，同时提供了适用于消息通信的高级特性，如轻量级的协议格式、主题订阅和消息分发机制。这些特点使MQTT非常适合物联网设备和应用，其中网络条件可能是挑战，而且资源经常是有限的。

 

## 7.Sparkplug B 和 MQTT

Sparkplug B 是建立在 MQTT 之上的一种规范，旨在提高工业物联网（IIoT）通信的互操作性和数据标准化。MQTT 提供了一种高效、灵活的消息传输机制，适用于多种用途和环境。相比之下，Sparkplug B 是为了在工业物联网领域中提高 MQTT 的互操作性和数据一致性，通过定义数据格式和通信模式，确保不同制造商的设备和应用可以更容易地集成和通信。简而言之，Sparkplug B 建立在 MQTT 的基础上，针对特定的应用场景提供了标准化的实现指南。

***\*MQTT\****

\- **基础协议**：MQTT 是应用层协议，它定义了消息的格式和传输方法，使得不同设备之间可以通过发布和订阅消息进行通信。

\- **灵活性**：提供了三种消息服务质量（QoS）等级，支持消息的可靠传输。

\- **简洁高效**：协议头部非常小，适用于所有类型的网络，特别是带宽有限和不稳定的网络环境。

\- **用途广泛**：被广泛应用于物联网（IoT）、移动应用、车辆通信系统等多个领域。

***\*Sparkplug B\****

\- **规范和框架**：Sparkplug B 是一个在 MQTT 之上的规范，为工业应用中的 MQTT 数据定义了一个标准化的主题命名空间、数据负载格式和状态记录。

\- **目的**：旨在解决MQTT在特定应用（如工业物联网）中的互操作性问题，确保设备和应用之间可以无缝通信，数据格式统一，便于集成和分析。

\- **特有特性**：引入了设备状态管理和数据报告的概念，支持设备生命周期管理，如出生证明（Birth）和死亡证明（Death）消息，用于设备状态监控和管理。

\- **针对性**：专为工业环境设计，解决特定行业的需求，比如实时生产数据监控、设备管理和预测性维护等。

 

## 8.常用相机格式

工业相机通常用于机器视觉和自动化系统中，它们捕捉的图像格式与普通消费型相机略有不同，主要是因为这些格式更适合进行实时处理和分析。以下是两种常见的工业相机图像格式：

- **RGB8**：这是一种颜色图像格式，其中每个颜色通道（红色、绿色和蓝色）各分配8位，总共24位。每个像素的颜色信息由这三个颜色通道的组合表示。RGB8格式直接提供颜色信息，便于图像处理和显示。这种格式在处理图像时相对直观，因为它直接反映了在常规显示设备上看到的颜色。24位/像素

- **Bayer**：这是一种常见的彩色滤镜阵列（CFA）格式，通常用在单个芯片彩色相机中。在Bayer格式中，每个像素只记录一个颜色——红、绿或蓝。因此，每个像素位置上只有单一颜色通道的信息。它依赖于Bayer模式，这种模式在绿色通道（对人眼更敏感）的采样频率比红色和蓝色更高。图像处理软件或固件需要使用去马赛克算法（demosaicing）来从Bayer图像重建完整的RGB图像。通常是8位、10位、12位或14位/像素
- **RAW格式**：RAW格式的位深度取决于图像传感器的分辨率和相机制造商的实现，通常是12位、14位或16位。例如，常见的RAW格式可能是12位或14位/像素。

**应用和处理**

- **应用**：工业相机广泛应用于自动化检测、机器人导航、质量控制等领域。这些应用通常需要快速的图像捕捉和处理能力。

- **处理**：对于Bayer格式，由于原始数据比完全的RGB图像数据量小，因此可以更快地传输和保存。然而，需要额外的处理步骤来解析成完整的彩色图像，这可能增加处理延迟。

  

## 9.数据库

```python
import psycopg2
# 连接数据库
def connect():
    try:
        conn = psycopg2.connect(
            dbname="your_dbname",
            user="your_username",
            password="your_password",
            host="your_host",
            port="your_port"
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
# 创建表
def create_table(conn):
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                age INTEGER,
                department VARCHAR(100)
            )
        ''')
        conn.commit()
        cur.close()
        print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
# 插入数据
def insert_data(conn, name, age, department):
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO employees (name, age, department)
            VALUES (%s, %s, %s)
        ''', (name, age, department))
        conn.commit()
        cur.close()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")
# 查询数据
def query_data(conn):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM employees')
        rows = cur.fetchall()
        for row in rows:
            print(row)
        cur.close()
    except Exception as e:
        print(f"Error querying data: {e}")
# 更新数据
def update_data(conn, emp_id, name=None, age=None, department=None):
    try:
        cur = conn.cursor()
        update_fields = []
        update_values = []
        if name:
            update_fields.append("name = %s")
            update_values.append(name)
        if age:
            update_fields.append("age = %s")
            update_values.append(age)
        if department:
            update_fields.append("department = %s")
            update_values.append(department)
        update_values.append(emp_id)
        cur.execute(f'''
            UPDATE employees
            SET {', '.join(update_fields)}
            WHERE id = %s
        ''', update_values)
        conn.commit()
        cur.close()
        print("Data updated successfully.")
    except Exception as e:
        print(f"Error updating data: {e}")
# 删除数据
def delete_data(conn, emp_id):
    try:
        cur = conn.cursor()
        cur.execute('''
            DELETE FROM employees
            WHERE id = %s
        ''', (emp_id,))
        conn.commit()
        cur.close()
        print("Data deleted successfully.")
    except Exception as e:
        print(f"Error deleting data: {e}")
# 关闭数据库连接
def close_connection(conn):
    if conn:
        conn.close()
        print("Database connection closed.")
# 主函数
if __name__ == "__main__":
    conn = connect()
    if conn:
        create_table(conn)
        # 插入示例数据
        insert_data(conn, "John Doe", 30, "HR")
        insert_data(conn, "Jane Smith", 25, "Finance")
        # 查询数据
        print("Current data in table:")
        query_data(conn)
        # 更新数据
        update_data(conn, 1, age=31)
        # 查询更新后的数据
        print("Data after update:")
        query_data(conn)
        # 删除数据
        delete_data(conn, 2)
        # 查询删除后的数据
        print("Data after deletion:")
        query_data(conn)
        # 关闭连接
        close_connection(conn)
```





# 开放问题

## 1.项目管理中如果有项目delay了怎么办

1. **识别原因**：以便更好的解决问题
2. **评估影响**：查看严重程度，决定资源调度范围
3. **制定应对策略**：重新分配资源，人员，时间
4. **经验教训总结**：结束后复盘

### 什么是一个好的项目管理？

一切技术问题都是进度问题，而进度问题本质上是人的问题。

不是个人能力不行，而是团队之间的氛围和人与人的关系问题。

最好的项管不是每天催进度，而是能够让大家的目标一致，主观能动性胜于一切。从催进度化身为带领队伍披荆斩棘的领头羊。当然我还差得远，但随着技术面的增加和管理经验的增加，能明显感觉到需要催进度的时候变少了。

周报、任务节点的设立肯定是有必要的，但这是把握进度的手段，而不是管理团队的方式。



## 2.熟悉客户端项目

设备原始数据----------->broker暂存----------->服务器、数据库---------->客户端

​						mqtt         			   订阅、传输、解码、存储		可视化

设备原始数据通过MQTT传输到broker暂存

当用户启用设备数据的传输功能的时候，自建的服务器会订阅broker的消息

用ID号区别设备，解析原始数据，并将解析的数据存入数据库

用户需要数据的时候，利用本地客户端从数据库拉取相关数据存入XLS



## 3.用过什么数据结构

队列 消息队列

​			
