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