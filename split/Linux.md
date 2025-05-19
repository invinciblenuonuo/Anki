# Linux



## Linux嵌入式驱动开发的流程

1. 了解硬件设备及其规范：首先要对目标硬件设备进行研究，包括芯片型号、外设接口、寄存器规范等。同时，对于设备的功能和特性也需要有基本的了解。
2. 编写设备树（Device Tree）描述文件：Linux内核使用设备树来描述硬件设备的信息。需要编写设备树描述文件，以便内核能够识别和配置硬件设备。
3. 编写驱动程序源码：根据设备的规格和需求，编写对应的驱动程序源码。通常需要涉及到底层寄存器的读写、中断处理、设备初始化和资源分配等操作。
4. 将驱动程序源码添加到内核源码树：将驱动程序源码添加到Linux内核源码树，并在内核配置选项中选择该驱动模块进行编译。
5. 构建并刷写内核镜像：完成驱动程序源码的添加和内核配置后，进行内核的构建。通过编译得到的内核镜像可以刷写到目标嵌入式设备上。
6. 调试和测试：将构建好的内核镜像刷写到目标设备，并进行调试和测试。检查设备与驱动之间的通信，确保驱动程序能够正确地初始化设备并提供所需的功能。
7. 优化和性能测试：根据实际使用情况对驱动程序进行优化，并进行性能测试。通过性能测试来评估驱动程序的性能，并进行必要的调整和优化。



##  Linux内核的组成

五部分：进程管理、内存管理、进程间通信、虚拟文件系统、网络接口

1.进程管理与调度：

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/70.png" alt="img" style="zoom: 67%;" />

2.内存管理：Linux内存管理对于每个进程完成从虚拟内存到物理内存的转换

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/70-16709318849786.png" alt="img" style="zoom:67%;" />

3.虚拟文件系统：隐藏硬件的细节，采用vfs_read，vfs_write等接口

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/70-16709319228729.png" alt="img" style="zoom: 67%;" />

4.网络接口：分为网络协议和网络驱动程序

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/70-167093197638612.png" alt="img" style="zoom:67%;" />

5.进程间通信：信号量、共享内存、消息队列、管道等，实现资源互斥、同步



## 系统调用read()  write()，内核具体做了哪些事情

用户空间read()-->内核空间sys_read()-->scull_fops.read-->scull_read()；

过程分为两个部分：用户空间的处理和内核空间的处理。

在用户空间中通过 0x80 中断的方式将控制权交给内核处理，

内核接管后，经过6个层次的处理最后将请求交给磁盘，由磁盘完成最终的数据拷贝操作。在这个过程中，调用了一系列的内核函数。



## 系统调用与普通函数调用的区别

| 类别     | 系统调用           | 函数调用               |
| -------- | ------------------ | ---------------------- |
| 简介     | 调用内核的服务     | 调用函数库中的一个程序 |
| 涉及对象 | 程序与内核         | 用户与程序             |
| 运行空间 | 内核地址空间       | 用户地址空间           |
| 开销     | 上下文切换，开销大 | 小                     |



## Bootloader内核 、根文件的关系

启动顺序：bootloader->linuxkernel->rootfile

u-boot：初始化硬件，将内核装载入RAM，设置SP与PC，准备启动内核

kernel：（底层驱动向内核注册，上层应用向内核调用）启动并挂载rootfile（存放了文件、库、命令）

rootfile：业务涉及的文件系统



## Bootloader启动过程

上电后运行的第一个程序：bootloader（u-boot）（universal bootloader）

- 典型嵌入式系统的部署：uboot程序（类似BIOS）部署在Flash(能作为启动设备的NorFlash)上、OS部署在FLash(嵌入式系统中用Flash代替了硬盘)上、内存在掉电时无作用，CPU在掉电时不工作。
- 启动过程：嵌入式系统上电后先执行uboot、然后uboot负责初始化DDR，初始化Flash，然后将OS从Flash中读取到DDR中，然后启动OS(OS启动后uboot就无用了) 总结：嵌入式系统和PC机的启动过程几乎没有两样，只是BIOS成了uboot，硬盘成了Flash。

Stage1（汇编实现，依赖cpu体系结构初始化）

​		进行硬件的初始化（watchdog,ram初始化）
​		为Stage2加载代码准备RAM空间
​		复制Stage2阶段代码到RAM空间
​		设置好栈
​		跳转到第二阶段代码的入口点

Stage2（c语言实现，具有好的可读性和移植性）

​		初始化该阶段所用到的硬件设备。
​		检测系统内存映射。
​		将uImage ,Rootfs，dtb文件从flash读取到RAM内存中。
​		设置内核启动参数。（如通过寄存器传递设备树文件的内存地址）



## Linux启动流程

1. 引导加载程序（Bootloader）启动：U-Boot 被加载到内存中执行。 U-Boot 提供了一个命令行界面，用户可以在这个界面上进行配置和操作。
2. 加载内核和备树文件：通过 U-Boot 的命令，加载 Linux 内核kernel）和设备树（device tree）文件到内存中4. 启动 Linux 内核：U-Boot控制权交给 Linux 内核，内核开始执行。内核会初始化系统硬设置页表、启动调度器等。
3. 启动 init 进：在内核初始化完成后，内核会执行 init 进程，init 进程是用户空间的第一个进程。 init 进程负责启动其他系统服务，并根据配置加载所需的模块。
4. 用户空间初始化：init 进程会根据配置启动用户空间的各个进程和服务，完成系统的初始化。



## 设备树

Linux设备树（Device Tree）是一种**描述硬件设备和设备间关系的数据结构**，用于在嵌入式系统中配置和管理硬件。它是**一种与平台无关的机制**，它将硬件设备的相关信息以一种可移植的格式储存在一个或多个设备树文件中。

设备树文件是以一种层级结构的形式描述硬件设备及其属性。它包含了设备的类型、寄存器地址、中断、时钟等信息，以及设备间的关系和依赖关系。通过解析设备树文件，内核可以获取设备的配置信息，并正确地初始化和管理硬件设备。



## Linux 命令

搜索：

​		grep *.c

​		grep -n "linux" test.txt  // 查找文件中的关键字并显示行号



搜索文件

​		find /home/user/dir -type f -name "*.c"

​		`-type f`表示只搜索文件，而不包括目录



查看文件内容：

​		cat：将原文显示



进程：

​		ps：查看进程

```
$ ps -ax
        PID TTY         STAT   TIME COMMAND
        1 ?     Ss      0:01 /usr/lib/systemd/systemd rhgb --switched-root --sys
        2 ?     S       0:00 [kthreadd]
        3 ?     I<      0:00 [rcu_gp]
        4 ?     I<      0:00 [rcu_par_gp]
```

​		pstree：查看父子进程关系

```
$ pstree -psn
systemd(1)─┬─systemd-journal(952)
        ├─systemd-udevd(963)
        ├─systemd-oomd(1137)
        ├─systemd-resolve(1138)
        ├─systemd-userdbd(1139)─┬─systemd-userwor(12707)
        │                     ├─systemd-userwor(12714)
        │                     └─systemd-userwor(12715)
        ├─auditd(1140)───{auditd}(1141)
        ├─dbus-broker-lau(1164)───dbus-broker(1165)
        ├─avahi-daemon(1166)───avahi-daemon(1196)
        ├─bluetoothd(1167)
```



内存占用：

​		free –h：系统相关RAM使用情况（物理内存、交换内存）

​		top：查看系统CPU、进程、内存使用情况



磁盘占用：

​		df -h：查看磁盘占用



关机、重启、挂起、节电：

​		shutdown -h now

​		shutdown -h +10  // 延时10min

​		shutdown -h 19:30

​		sudo reboot

​		sudo pm-suspend

​		sudo pm-powersave



## 手动释放内存的方法

采用TOP命令查看内存张后，采用/proc/sys/vm/drop_caches来释放内存

`[root@ipa]# echo 0~3 > /proc/sys/vm/drop_caches` 

**drop_caches的值可以是0-3之间的数字，代表不同的含义：**
0：不释放（系统默认值）
1：释放页缓存
2：释放dentries和inodes
3：释放所有缓存



## 文件系统

![image-20230706162608465.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230706162608465.png)



## 查看程序依赖的动态链接库

```c++
#include <stdio.h>
#include <iostream>
#include <string>
using namespace std;
 
int main ()
{
   cout << "test" << endl;
   return 0;
}

# g++ -o demo main.cpp
# ldd demo  // 查看依赖的动态链接库文件
    linux-vdso.so.1 => (0x00007fffcd1ff000)
        libstdc++.so.6 => /usr/lib64/libstdc++.so.6 (0x00007f4d02f69000)
        libm.so.6 => /lib64/libm.so.6 (0x00000036c1e00000)
        libgcc_s.so.1 => /lib64/libgcc_s.so.1 (0x00000036c7e00000)
        libc.so.6 => /lib64/libc.so.6 (0x00000036c1200000)
        /lib64/ld-linux-x86-64.so.2 (0x00000036c0e00000)
```

如果程序引入动态链接库，但没有使用，一样会被链接，且影响启动速度，下面的例子

```c++
# g++ -o demo -lz -lm -lrt main.cpp  // 加入用不到的.so
# ldd demo
        linux-vdso.so.1 => (0x00007fff0f7fc000)
        libz.so.1 => /lib64/libz.so.1 (0x00000036c2600000)
        librt.so.1 => /lib64/librt.so.1 (0x00000036c2200000)
        libstdc++.so.6 => /usr/lib64/libstdc++.so.6 (0x00007ff6ab70d000)
        libm.so.6 => /lib64/libm.so.6 (0x00000036c1e00000)
        libgcc_s.so.1 => /lib64/libgcc_s.so.1 (0x00000036c7e00000)
        libc.so.6 => /lib64/libc.so.6 (0x00000036c1200000)
        libpthread.so.0 => /lib64/libpthread.so.0 (0x00000036c1a00000)
        /lib64/ld-linux-x86-64.so.2 (0x00000036c0e00000)
            
# ldd -u demo  // 查看没有用到的.so
Unused direct dependencies:
        /lib64/libz.so.1
        /lib64/librt.so.1
        /lib64/libm.so.6
        /lib64/libgcc_s.so.1
```





## 软连接、硬连接

系统中只有一份数据，若一个用户修改，其他用户可以同步感知

硬链接：通过索引节点来进行链接。磁盘中的文件具有的索引编号（Inode）（允许一个文件拥有多个有效路径名）

![824470-20180531151753197-400006785.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/824470-20180531151753197-400006785.png)

1. 以文件副本的形式存在。但不占用实际空间。
2. 不允许给目录创建硬链接。
3. 硬链接只有在同一个文件系统中才能创建。
4. 删除其中一个硬链接文件并不影响其他有相同 inode 号的文件。
5. 不同用户看来文件名可以不同

软连接：（符号连接，快捷方式）软链接就是一个普通文件，存放另一文件的路径

1. 软链接是存放另一个文件的路径的形式存在。
2. 可以跨文件系统 
3. 可以对一个不存在的文件名进行链接，硬链接必须要有源文件。
4. 可以对目录进行链接。

```shell
[oracle@Linux]$ touch f1          #创建一个测试文件f1  原有文件
[oracle@Linux]$ ln f1 f2          #创建f1的一个硬连接文件f2  ln 源地址 目标地址
[oracle@Linux]$ ln -s f1 f3       #创建f1的一个符号连接文件f3  ln -s 源地址 目标地址
[oracle@Linux]$ ls -li            # -i参数显示文件的inode节点信息
total 0
9797648 -rw-r--r--  2 oracle oinstall 0 Apr 21 08:11 f1
9797648 -rw-r--r--  2 oracle oinstall 0 Apr 21 08:11 f2
9797649 lrwxrwxrwx  1 oracle oinstall 2 Apr 21 08:11 f3 -> f1
#硬连接文件 f2 与原文件 f1 的 inode 节点相同，均为 9797648，然而符号连接文件的 inode 节点不同。
```

```shell
[oracle@Linux]$ echo "I am f1 file" >>f1
[oracle@Linux]$ cat f1
I am f1 file
[oracle@Linux]$ cat f2
I am f1 file
[oracle@Linux]$ cat f3
I am f1 file
[oracle@Linux]$ rm -f f1
[oracle@Linux]$ cat f2
I am f1 file
[oracle@Linux]$ cat f3
cat: f3: No such file or directory
#当删除原始文件 f1 后，硬连接 f2 不受影响，但是符号连接 f3 文件无效
```

![image-20230706161728700.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230706161728700.png)



## Linux权限

文件角色有3种：

- 文件拥有者 ：谁创建这文件谁就是拥有者；
- 文件所属组 ：所有用户都要隶属于某一个组，哪怕只有一个人；
- 其他人 ：除了拥有者之外的人都是other。

**更改拥有者 ：** 需要 sudo 提升到管理员身份才能修改

**更改所属组 ：**sudo [chgrp](https://so.csdn.net/so/search?q=chgrp&spm=1001.2101.3001.7020) yz func.c 

权限数字定义

- rwx = 4 + 2 + 1 = 7

- rw = 4 + 2 = 6

- rx = 4 +1 = 5


即

- 若要同时设置 rwx (可读写运行） 权限则将该权限位 设置 为 4 + 2 + 1 = 7

- 若要同时设置 rw- （可读写不可运行）权限则将该权限位 设置 为 4 + 2 = 6

- 若要同时设置 r-x （可读可运行不可写）权限则将该权限位 设置 为 4 +1 = 5



## 设备驱动

![image-20230708115833093.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230708115833093.png)

逻辑设备表

<img src="https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230708115847593.png" alt="image-20230708115847593" style="zoom:50%;" />

记录了逻辑设备名称与物理设备名称的对应关系以及驱动程序入口地址



## 字符设备、块设备、网络设备

![image-20230708120156845.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230708120156845.png)



## socket

用户建立一个socket，指明网络协议、端口号等，在内核中开辟一个空间，返回句柄fd

用户将数据包用write系统调用传给内核，内核调用网卡驱动发送出去

对端主机反向处理数据，应用采用read系统调用读取

![image-20230708125052374.png](https://obsidian-1321127127.cos.ap-beijing.myqcloud.com/image-20230708125052374.png)



## grep

```shell
grep "^a" a.txt   ## 查找以a开头的行
grep "^a.*r$" a.txt   ## 同时查找以a开头同时以r结尾的行
grep "^a.*h.*r$" a.txt  ## 同时查找以a开头，包含字符h，并以r结尾的行
grep "^a\|e$" a.txt  ## 提取以a开头，或者以e结尾的行

\ 反义字符：如"\"\""表示匹配""
[ - ] 匹配一个范围，[0-9a-zA-Z]匹配所有数字和字母
* 所有字符，长度可为0
+ 前面的字符出现了一次或者多次
^ #匹配行的开始 如：'^grep'匹配所有以grep开头的行。
$ #匹配行的结束 如：'grep$'匹配所有以grep结尾的行。
. #匹配一个非换行符的字符 如：'gr.p'匹配gr后接一个任意字符，然后是p。
* #匹配零个或多个先前字符 如：'*grep'匹配所有一个或多个空格后紧跟grep的行。
.* #一起用代表任意字符。
[] #匹配一个指定范围内的字符，如'[Gg]rep'匹配Grep和grep。
[^] #匹配一个不在指定范围内的字符，如：'[^A-FH-Z]rep'匹配不包含A-R和T-Z的一个字母开头，紧跟rep的行。
\(..\) #标记匹配字符，如'\(love\)'，love被标记为1。
\< #到匹配正则表达式的行开始，如:'\<grep'匹配包含以grep开头的单词的行。
\> #到匹配正则表达式的行结束，如'grep\>'匹配包含以grep结尾的单词的行。
x\{m\} #重复字符x，m次，如：'0\{5\}'匹配包含5个o的行。
x\{m,\} #重复字符x,至少m次，如：'o\{5,\}'匹配至少有5个o的行。
x\{m,n\} #重复字符x，至少m次，不多于n次，如：'o\{5,10\}'匹配5--10个o的行。
\w #匹配文字和数字字符，也就是[A-Za-z0-9]，如：'G\w*p'匹配以G后跟零个或多个文字或数字字符，然后是p。
\W #\w的反置形式，匹配一个或多个非单词字符，如点号句号等。
\b #单词锁定符，如: '\bgrep\b'只匹配grep。
```



## 文件大小写转换

```shell
cat file | tr a-z A-Z > newfile #将文件内容转换为大写
```



## LInux是否支持浮点运算

Linux kernel默认不支持浮点计算。因为浮点相关寄存器(浮点计算上下文)在系统调用（进程切换）的过程中不会被保存，出于进程切换效率的考虑



## Linux的7种文件类型

1. 普通文件类型

    Linux中最多的一种文件类型, 包括 纯文本文件；二进制文件；数据格式的文件；各种压缩文件。第一个属性为 [-]

2. 目录文件

    就是目录， 能用 cd 命令进入的。第一个属性为 [d]

3. 块设备文件

    块设备文件 ： 硬盘。例如一号硬盘的代码是 /dev/hda1等文件。第一个属性为 [b]

4. 字符设备

    即串行端口的接口设备，例如键盘、鼠标等等。第一个属性为 [c]

5. 套接字文件

    这类文件通常用在网络数据连接。可以启动一个程序来监听客户端的要求，客户端就可以通过套接字来进行数据通信。第一个属性为 [s]，最常在 /var/run目录中看到这种文件类型

6. 管道文件

    FIFO也是一种特殊的文件类型，它主要的目的是，解决多个程序同时存取一个文件所造成的错误。第一个属性为 [p]

7. 链接文件

    类似Windows下面的快捷方式。第一个属性为 [l]



## Cortex-M能否运行Linux

不能，其不存在硬件的MMU（内存管理单元）（将硬件物理地址映射到虚拟地址并做检查）

STM32MP1（Cortex-A7）可运行Linux



## shell脚本语法与命令

```shell
#!/bin/bash
echo "Hello World !"  # 打印输出
your_name="runoob.com"  # 定义变量

```



