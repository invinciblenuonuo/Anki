# STM32

## STM32启动流程

1.依据boot引脚选择启动区域

| 引脚 | 启动方式   | 描述                                           |
| ---- | ---------- | ---------------------------------------------- |
| x 0  | 片内Flash  | 代码区启动，ICP下载（SWD、JTAG烧录）           |
| 0 1  | 系统存储器 | 内置ROM启动，ISP下载（出厂预置代码，UART烧录） |
| 1 1  | SRAM       | RAM启动，掉电丢失                              |

2.运行bootloader

![watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3FxXzQxNjc3ODE1,size_16,color_FFFFFF,t_70#pic_center.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark2.png)

​	处理器会将各个寄存器的值初始化为默认值

​	2.1 硬件设置SP、PC，进入复位中断函数Rest_Hander()

​		从0x0800 0000读取数据赋值给栈指针SP(MSP)，设置为栈顶指针0x2000 0000+RAM_Size

​		从0x0800 0004读取数据赋值给PC（指向Reset_Handler中断服务函数）

```c
LDR R0, = SystemInit
BLX R0 
```

​	2.2 设置系统时钟，进入SystemInit()

​		设置RCC寄存器各位

​		设置中断向量表偏移地址

```c
#ifdef VECT_TAB_SRAM
  SCB->VTOR = SRAM_BASE | VECT_TAB_OFFSET; /* Vector Table Relocation in Internal SRAM. */
#else
  SCB->VTOR = FLASH_BASE | VECT_TAB_OFFSET; /* Vector Table Relocation in Internal FLASH. */
#endif 
```

​	2.3 软件设置SP，__main入栈（统初始化函数）

```c
LDR R0,=__main
BX R0
```

​	2.4 加载data、bss段并初始化_main栈区

​		拷贝Flash中的数据进入SRAM（哈弗体系结构决定了：数据与代码分开存储）

​		![0ea95a362db5457185191faf18069262.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/0ea95a362db5457185191faf18069262.png)

3 跳转到main()

![v2-1224644e63357ad886348dd630d9bce7_720w.webp](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/v2-1224644e63357ad886348dd630d9bce7_720w.webp)

![image-20230714215157086.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230714215157086.png)



### OTA的情况

![image-20230714215350653.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230714215350653.png)

在FLASH中添加引导程序后，其与APP程序将各自对应一个中断向量表，假设引导程序占用N+M Byte的FLASH空间。上电后，单片机从复位中断向量表处获取地址，并跳转执行复位中断服务函数，执行完毕后执行主函数，随后执行Bootloader中程序跳转的相关代码跳转至APP，即地址0x08000004+N+M处。进入主函数的步骤与Bootloader函数一致。当运行在主函数时，若有中断请求被响应，此时PC指针本应当指向位于地址0x08000004处的中断向量表，但由于程序预先通过“SCB->VTOR = 0x08000000 | ADDR_OFF;”这一语句，使得中断向量表偏移ADDR_OFF（N+M）地址，因此PC指针会跳转到0x08000004+N+M处所存放的中断向量表处，随后执行本应执行的中断服务函数，在跳出函数后再进入主函数运行。

![20190221125313717.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/20190221125313717.png)

```c
void iapLoadApp(uint32_t appxAddr)
{
	iapfun jumptoapp;
	if( 0x20000000 == ( (*(vu32*)appxAddr) & 0x2FFE0000) )//检查appxaddr处存放的数据(栈顶地址0x2000****)是不是在RAM的地址范围内
	{ 
		jumptoapp = (iapfun)*(vu32*)(appxAddr + 4);//拷贝APP程序的复位中断函数地址，用户代码区第二个字为程序开始地址(复位地址)（强制跳转到函数地址处执行，函数指针的方式）
		MSR_MSP(*(vu32*)appxAddr);//初始化APP堆栈指针(用户代码区的第一个字用于存放栈顶地址)，重新分配RAM
		jumptoapp();//执行APP的复位中断函数，跳转到APP
	}
}	
```



## 中断的过程

中断初始化

1. 设置中断源，让某个外设可以产生中断；

2. 设置中断控制器，使能/屏蔽某个外设的中断通道，设置中断优先级等；

3. 使能CPU中断总开关


CPU在运行正常的程序

产生中断，比如用户按下了按键 —> 中断控制器 —> CPU

**CPU每执行完一条指令（指令有多个时钟周期，取指、译码、执行等）都会检查是否有异常/中断产生**

发现有异常/中断产生，开始处理：

1. 保存现场（PC、LR、MSP、通用寄存器、FPU压栈）

2. 分辨异常/中断，调用对应的异常/中断处理函数

3. 恢复现场（PC与出栈）



在执行高优先级中断时如果低优先级中断到来，低优先级中断不会被丢失

当中断发生时，PC设置为一个特定地址，这一地址按优先级排列就称为异常向量表





## STM32定时器

系统滴答定时器`SysTick`（并非外设，CM3内核）

看门狗定时器`WatchDog`

基本定时器`TIM6,TIM7`

通用定时器`TIM2,TIM3,TIM4,TIM5`（输出比较、输入捕获、PWM、单脉冲）

高级定时器`TIM1,TIM8`（死区控制）

基本定时：预分频、重装载寄存器

PWM：预分频、重装载、比较寄存器



## STM32 ADC

STM32F1 ADC，精度为12位，每个ADC最多有16个外部通道，各通道的A/D转换可以单次、连续扫描或间断执行，ADC转换的结果（6-12位）可以左对齐或右对齐储存在16位数据寄存器中。ADC的输入时钟不得超过14MHz，其时钟频率由PCLK2分频产生。

一个ADC的不同通道读取的值在共用的DR寄存器中，进行下一个通道采集前需要将数据取走否则丢失

注入通道：可以在规则通道转换时，强行插入转换

参考电压：3.3V

采集精度与位数：最大测量电压/2^采样位数，例如3.3V / 2^12，采样逐次逼近

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20221209182245687.png" alt="image-20221209182245687" style="zoom: 50%;" />

精度 

实际值和采样值的偏差



分辨率

10cm长的尺子，最小刻度是1mm，分辨率是1mm

由采样位数决定。一个12位的ADC可以将输入电压转换为4096个离散的数值（2^12 = 4096）



## STM32 DMA

当外部设备（如硬盘、显卡、网络适配器等）需要与主存储器进行数据交换时，需要通过中央处理器（CPU）作为中介来完成数据传输操作。然而，在大量数据传输的情况下，这样的方式会造成CPU过多地参与数据传输，降低了整体性能。

CPU将外设数据搬运到内存的顺序：

1. 外设设置状态寄存器置位
2. CPU读取外设数据寄存器到CPU通用寄存器
3. CPU将通用寄存器数据写入内存

CPU不介入情况下，将数据在外设与内存中传递

![image-20230706174634517.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230706174634517.png)

DMA配置：数据宽度（u8 u16 u32），数据量(sizeof)，数据地址

循环模式：单轮传输结束后，重置传输计数器，重置传输地址为初始值，再次开始新一轮循环

双缓冲区：一个缓冲区传输完成中断触发后，缓存地址乒乓交换，同时触发回调函数

DMA会节约总线资源吗（不能，他只是节约了CPU）



DMA配置

1. 配置DMA控制器：设置DMA通道、数据传输方向（外设到存储器或存储器到外设）、传输模式（单次传输、循环传输等）、数据宽度、传输计数等参数
2. 分配内存：如果是外设到存储器的数据传输，需要分配一块足够大小的缓冲区
3. 配置DMA通道：将外设和DMA通道连接起来，通常需要配置外设的DMA请求触发方式和DMA通道的优先级等参数。
4. 触发DMA传输：启动数据的传输。DMA控制器将自动执行数据的传输，而不需要CPU的干预。



**实际应用**

- 分析性能瓶颈在哪，是数据频率还是数据量过大
- 数据频率：双DMA BUF
- 数据量：单个大 DMA BUF



## STM32中断

定义：正在执行某事件时，被某事件打断，造成任务切换

分类：内核异常、外部中断

嵌套向量中断控制器NVIC：多个优先级中断到来后的处理顺序

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3FxXzI5OTk2Mjg1,size_16,color_FFFFFF,t_70-16709870095783.png" alt="img" style="zoom:67%;" />

处理流程：CPU收到(interrupt request，IRQ)后，通过上下文切换保存当前工作状态，跳转至中断处理函数执行（中断向量表），完成后再出栈执行原有程序



## 中断和异常

相同点：都是CPU对系统发生的某个事情做出的一种反应

区别：中断由外因引起，异常由CPU本身原因引起

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3FxXzI5OTk2Mjg1,size_16,color_FFFFFF,t_70.png" alt="img" style="zoom:67%;" />



## STM32看门狗

定时喂狗，否则触发系统复位

IWDG独立看门狗：采用独立时钟，监视硬件错误

WWDG窗口看门狗：采用系统时钟，监视软件错误（必须在规定时间窗口刷新）（防止跑飞后跳过某些代码段）（进入WWDG中断时，可以保存复位前的数据）



## IO口类型

| 分类     | 电平                                                         | 用途       | 备注                                                         |
| -------- | ------------------------------------------------------------ | ---------- | ------------------------------------------------------------ |
| 上拉输入 | 常态高电平（上拉电阻连接VCC）                                | IO读取     |                                                              |
| 下拉输入 | 常态低电平（下拉电阻连接GND）                                | IO读取     |                                                              |
| 推挽输出 | 可以输出高电平和低电平，都有较强驱动能力，IO输出0-接GND， IO输出1 -接VCC | 一般IO输出 | 驱动负载能力强                                               |
| 开漏输出 | 只能输出低电平，高电平没有驱动能力，需要外部上拉电阻才能真正输出高电平 | 线与功能   | 像IIC中，只要有一个给低电平，那么总线都会被拉低。实现线与功能 |



## STM32 主频、Flash、SRAM大小

| 类型          | 主频 | Flash  | RAM   | 内核 |
| ------------- | ---- | ------ | ----- | ---- |
| STM32F407IGH6 | 168M | 1024KB | 192KB | M4   |
| STM32L151RET6 | 32M  | 512KB  | 80KB  | M3   |
| STM32F103C8T6 | 72M  | 64KB   | 20KB  | M3   |
| HC32L130E8PA  | 48M  | 64KB   | 8KB   | M0+  |



## ADC采样原理

逐次逼近转换过程和用天平称物重非常相似。天平称重物过程是，从最重的砝码开始试放，与被称物体进行比较，若物体重于砝码，则该砝码保留，否则移去。再加上第二个次重砝码，由物体的重量是否大于砝码的重量决定第二个砝码是留下还是移去。照此一直加到最小一个砝码为止。将所有留下的砝码重量相加，就得此物体的重量。仿照这一思路，逐次比较型A/D转换器，就是将输入模拟信号与不同的参考电压作多次比较，使转换所得的数字量在数值上逐次逼近输入模拟量对应值。

![25999089-20433dbc3f0a1fe5.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/25999089-20433dbc3f0a1fe5.png)



## ARM 汇编

```assembly
LDR #从存储器中将一个32位的字数据传送到目的寄存器中。该指令通常用于从存储器中读取32位的字数据到通用寄存器，然后对数据进行处理。
LDR  R0,[R1]           # 将存储器地址为R1的字数据读入寄存器R0
LDR  R0,[R1, #8]        // 将存储器地址为R1+8的字数据读入寄存器R0
LDR  R1,  [R0,#0x12] # 将R0+0x12 地址处的数据读出，保存到R1中(R0 的值不变)
LDR  R1,  [R0,R2] # 将R0+R2 地址的数据计读出，保存到R1中(R0 的值不变)
```



```assembly
STR #从源寄存器中将一个32位的字数据传送到存储器中，使用方式可参考指令LDR
STR R0,[R1]  # 将R0寄存器的数据写入R1地址的内存
STR R0,[R1, #8]  # 将R0中的字数据写入以R1＋8为地址的存储器中
STR R0,[R1],#8  # 将R0中的字数据写入以R1为地址的存储器中，并将新地址R1＋8写入R1
```



```assembly
MOV   R1    #0x10 ;               # R1=0x10 将数值放入R1
MOV   R0,    R1 ;                 # R0=R1 将寄存器值放入R1
MOVS  R3,   R1,  LSL  #2 ;         R3=R1＜＜2，并影响标志位
```