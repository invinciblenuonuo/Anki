# Cortex-M

## 寄存器

Cortex-M 系列 CPU 的寄存器组里有 R0~R15 共 16 个通用寄存器组和若干特殊功能寄存器

SP指向：栈顶

LR指向：函数调用结束后的返回地址

PC指向：下一条指令

![09interrupt_table.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/09interrupt_table.png)

寄存器R13在ARM指令中常用作堆栈指针SP，寄存器R14称为子程序链接寄存器LR(LinkRegister)，寄存器R15用作程序计数器(PC)。
ARM微处理器共有37个32位寄存器，其中31个为通用寄存器，6个位状态寄存器。通用寄存器R0~R14、程序计数器PC（即R15）是需要熟悉其功能的。



## R13 SP MSP PSP

MSP的含义是Main_Stack_Pointer，即主栈
PSP的含义是 Process_Stack_Pointer,即任务栈

- Cortex-M3内核中有两个堆栈指针（MSP & PSP），但任何时刻只能使用到其中一个。
- 复位后处于线程模式特权级，默认使用MSP。
- 通过SP访问到的是正在使用的那个指针，可以通过MSR/MRS指令访问指定的堆栈指针。
- 通过设置CONTROL寄存器的bit[1]选择使用哪个堆栈指针。CONTROL[1]=0选择主堆栈指针；CONTROL[1]=1选择进程堆栈指针。
- Handler模式下，只允许使用主堆栈指针MSP。

典型的OS环境中，MSP和PSP的用法如下：

- MSP用于OS内核和异常处理。
- PSP用于应用任务。
- CONTROL的bit1为0，SP = MSP
    CONTROL的bit1为1，SP = PSP

在裸机开发中，CONTROL的bit1始终是0，也就是说裸机开发中全程使用程MSP，并没有使用PSP。在执行后台程序(大循环程序)SP使用的是MSP，在执行前台程序(中断服务程序)SP使用的是MSP。
在OS开发中，当运行中断服务程序的时候CONTROL的bit1是0，SP使用的是MSP；当运行线程程序的时候CONTROL的bit1是1，SP使用的是PSP。

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/77adfd6d116646938be68957e77dc2b1.png" alt="在这里插入图片描述" style="zoom: 50%;" />

![333765-20190729152749256-654379342.jpg](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/333765-20190729152749256-654379342.jpg)

初始化时的操作

- 系统复位时从0x00000000处读出MSP的初始值。
- 在OS初始化时，对PSP进行初始化。

![333765-20190729153022824-1935836660.jpg](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/333765-20190729153022824-1935836660.jpg)

任务调度时的操作

- 用任务A的SP执行入栈操作，并保存任务A的SP。
- 设置PSP指向任务B的栈空间，用任务B的SP执行出栈，随后开始执行任务B。

![333765-20190729153108482-487805476.jpg](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/333765-20190729153108482-487805476.jpg)





## 用户级和特权级

Cortex-M分为两个运行级别

处理模式：异常与中断，工作在特权级

线程模式：其他情况，可以工作在用户级和特权级

![09interrupt_work_sta.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/09interrupt_work_sta.png)



## NVIC（嵌套向量中断控制器）

NVIC支持中断嵌套功能。当一个中断触发并且系统进行响应时，处理器硬件会将当前运行位置的上下文寄存器自动压入中断栈中，这部分的寄存器包括 PSR、PC、LR、R12、R3-R0 寄存器

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/09relation.png" alt="Cortex-M 内核和 NVIC 关系示意图" style="zoom:67%;" />



## M3 M4对比

M4新增FPU浮点

相较于M3用软件方式计算浮点，硬件浮点计算更快

![20180227201116208.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20180227201116208.png)
