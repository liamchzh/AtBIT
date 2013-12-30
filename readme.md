#「[人在北理](http://atbit.org/)」

### 1.安装MySQL,virtualenv,pip

### 2.激活虚拟环境(virturalenv)

    mkdir /path/to/yourproject
    cd /path/to/yourproject
    virtualenv --distribute venv
    . venv/bin/activate

### 3.克隆代码并安装所要的包

    git clone git@github.com:liamchzh/atbit.git  
    
    pip install -r requirements.txt

### 4.导入SQL数据

数据表是atbit.sql。进入MySQL后使用source命令导入。

### 5.运行
按照[这篇文章](http://saepy.sinaapp.com/topic/21/%E8%BD%BB%E6%9D%BE%E6%90%AD%E5%BB%BAsae-python-%E6%9C%AC%E5%9C%B0%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83)搭建好SAE本地环境，注意我用的tornado版本是2.4.1。需要下载官方的安装文档，修改其中的/dev_server/setup.py，然后在该目录运行`python setup.py install`

然后回到「人在北理」根目录运行：  

    
    python dev_server.py --mysql=username:password@localhost:3306  # username是你MySQL的用户名，一般是root，password则为密码
    
- - - - - - - 
有疑问随时联系liamchzh@gmail.com
