# Developer Guide

```
谢森煜 刘嘉诚 李展发 Modified November 12
```
Github代码仓库：https://github.com/SenyuXie/tripsphere

Apifox项目：https://app.apifox.com/project/

#### 📌 请大家遵守相关开发规范，若规范存在不合理之处及时在群里反馈

## HOWTO

## Python开发

第一步，先安装一下uv，详见https://docs.astral.sh/uv/。

第二步，配置/同步一下开发环境，请务必确保所有依赖管理都用uv进行。

如果是维护一个已经发布了的Python服务/Agent，直接cd到对应的目录下然后执行uv sync即可，
如果服务/Agent的pyproject.toml中还声明了optional-dependencies（比如声明了一组名
为"foo"的可选依赖），在同步依赖的时候也可按需加上，如uv sync --extra foo。

如果是要新建一个服务/Agent，则根据需求用uv init。然后像Python开发规范-Protobuf中提到的
需要一个空的tripsphere包作为占位，可以抄trip-chat-service这个服务里面的。

一般情况下，你可能还需要在本地开发环境起Nacos-server和Otel-collector，当然还有数据库啥的。

第三步，梳理业务逻辑/熟悉已有代码。

如果是熟悉代码，一般可以从gRPC Servicer入手，自顶向下逐层深入。开发前主要是先搞清楚业务逻
辑的生命周期、状态管理、涉及的服务/实体/值对象/聚合等。

开发Agent的话需要明确采用的Agent架构、设计模式、工具调用、知识库等。

第四步，根据需求添加或修改代码。

## Java开发

## Go开发


### TypeScript开发

## 目录结构说明

### Monorepo

各个微服务存放在一个独立的目录下，独立打包，名字统一为"trip-xxx-service"，例如"trip-chat-
service"。

各个Agent也放在一个独立的目录下，独立打包，名字一般为"trip-abc-xyz[er/or]"，例如"trip-
itinerary-planner"。

仓库的组织参考了https://github.com/FudanSELab/train-ticket/tree/master，但是不用maven的
submodule，不用uv的workspace，也就是说单个服务单个目录单个module，仓库根目录不出现
pom.xml、pyproject.toml等。

### Libs

#### v2-stubs

stubgen自动生成的对v2.nacos这个包的type stubs，人工补充了部分类型注解。为python微服务中使
用了Nacos v2 API的代码提供类型注解，帮助你通过mypy和pyright的静态类型检查。如果持续使用
Nacos v2 API，且官方sdk类型注解一直没有完善，那么这个type stubs库就需要长期维护，包括但不
限于重新stubgen生成或人工补充类型注解到生成的.pyi文件中。

### Contracts

#### Protobuf

整个项目的.proto文件被放在contracts/protobuf下，每个微服务/Agent都是比较独立的，各个微服
务/Agent之间唯一的联系就是gRPC/A2A/HTTP这种协议上的网络通讯，不存在超出自己目录外的引用
依赖。这里的引用依赖是指runtime的依赖，开发态的依赖（如依赖了libs/v2-stubs这个type stubs
库）是被允许的。

同时我希望各个服务docker build的上下被限制在自己的那个目录下。参考OpenTelemetry Demo
（https://github.com/open-telemetry/opentelemetry-demo/tree/main）的实践方式，我们需要在开
发/测试/编译/构建/打包之前，把contracts/protobuf下的.proto拷贝到自己微服务所属的目录下，然
后你就可以在自己的目录下愉快地玩耍了。

TL;DR

不存在你的代码从根目录下某目录导入一个包作为运行时依赖的情况。开发时把contracts/protobuf下
的.proto文件拷到自己的微服务目录下去（具体拷到哪&怎么用，见各个语言的开发规范），当（你/
别人）更新了contracts/protobuf后，及时重新拷贝这些.proto文件。


#### OpenAPI

### CHANGELOG.md

```
Please update changelog as part of any significant pull request. Place short description of your
change into "Unreleased" section. During the release process, the "Unreleased" section content
is used to generate the release notes.
```
鉴于目前我们还在内部快速迭代阶段，并不存在pull request，所以我们只要在某次实现核心功能的重
大提交中顺便更新一下这个文件的"# Unreleased"就可以了（简短的描述即可，尽量不要太长）。格
式大致为：

```
CHANGELOG.md
```
- trip-chat-service:
- Conversation management based on Agent2Agent protocol
- trip-itinerary-planner:
- LLM-powered itinerary planning using LangGraph and OpenAI
- Human-in-the-Loop functionality for user feedback and adjustments

等后续v0.1.0版本发布之后，我们就可以不需要按照这种格式，每一次Major release/Minor
release/Patch release可以类似https://github.com/open-telemetry/opentelemetry-
demo/blob/main/CHANGELOG.md这样平铺成列表。

如果有重大更新，可以再具体重新组织内容格式。

### Makefile

### docker-compose.yaml

docker compose配置文件，目前仅仅用于开发环境，如果你的本地开发环境有docker&docker
compose，可以通过docker compose -f ./docker-compose.yaml up快速启动一个nacos-
server容器和一个opentelemetry-collector容器。

## 接口定义

### Protobuf

我们在Github仓库中通过.proto文件和.yaml/.json格式的OpenAPI文件维护接口定义，gRPC的
Protobuf统一存放在contracts/protobuf/下。

```
1
2
3
4
5
```

以trip-note-service为例，若要更新/获取服务接口，统一依赖/contracts/protobuf下的文件，在项目根
目录执行make refresh-protos SERVICE=trip-note-service，接着cd进自己的服务目录
再重新生成gRPC code（或者直接在项目根目录执行make compile-protos SERVICE=trip-
note-service）。

### OpenAPI

我们在Github仓库中通过.proto文件和.yaml/.json格式的OpenAPI文件维护接口定义，OpenAPI文档统
一存放在contracts/openapi/下。另外可以通过Apifox进行接口文档协作：
https://app.apifox.com/project/7147228。

## 构建打包

### Dockerfile

Dockerfile里不能直接用（本地开发时）编译好的gRPC代码，而是要依赖于原始的.proto文件并重新
编译。

以trip-note-service为例，.proto文件需要事先拷贝到微服务目录下（项目根目录的Makefile和
scripts/可能可以帮到你）。这个拷贝操作可以是在本地开发时手动进行，也可以是CI/CD流水线
镜像build前进行（这样构建上下文就可以限制在trip-note-service/这个目录下了）。

.proto文件的编译根据语言的不同有不同的指令，可以参考样板在具体服务目录下手动执行命令，也
可以在项目的根目录执行make compile-protos SERVICE=trip-note-service，或者可以
在项目根目录执行scripts/compile-protos.sh trip-note-service。

## 服务注册与发现

往Nacos注册服务实例时，服务的名称统一使用"trip-abc-service"这种格式的名字。

## 统一规范

### 让我们一起说英文

##### 代码中所有的文档、注释、消息统一都使用英文（英语不好就用AI或者谷歌翻译），数据库里的数据

则可以包含中文。前端页面的语言我们也统一使用英文，后续如果有余力再做i18n。

### Git提交信息

提交信息模板：<type>: <subject>，规范要求：

- <type>后接英文冒号和一个空格，然后接<subject>。^
- <subject>部分由1~3句完整的英文句子组成（开头字母大写，结尾使用英文标点符号）。^

例如：feat: Add protobuf definitions for itinerary service.


<type>主要使用以下几种类型：

```
1. feat：新功能开发，例如你实现了某个核心业务流程，或业务流程的子模块
2. fix：修复bug，例如你修复了聊天服务某个接口无法返回预期结果的bug
3. test：测试相关，例如你修改/添加了测试用例，或对pytest等测试工具进行了配置
4. refactor：重构代码（没有添加新功能/修bug），例如修改类的名字、调整模块划分等
5. style：代码格式调整，例如你使用ruff format对代码进行了格式化
6. docs：文档变动，主要针对README.md等文档的更新，如果只是添加了注释也可以用这个
<type>
7. perf：性能优化，例如你优化了某个核心算法，或者优化了某个业务流程
8. chore：构建流程、工具、依赖库等的变动，例如更新Dockerfile、更新.proto文件、添加依赖
等
9. merge：代码合并，不添加这个<type>也可以，因为一般git会自动生成类似"Merge branch
'develop' of https://github.com/SenyuXie/tripsphere into develop"的消息
10. ......
```
实际开发中以本次提交的主要目的为准选择<type>，尽量不将多种意图的提交混在一起，如果迫不
得已混在一起，请务必在<subject>中说明清楚，例如feat: Implement memory mechanism
for chat service. Update protobuf of tripsphere/chat. 。<subject>的要求不必严
格遵守，但是要能让人看懂你提交了啥。

### Git分支管理

开发代码统一提交到develop分支上，请勿直接提交到main分支上。后续通过手动merge&push或更正
式的pull request将代码合入主分支上。

### Pre-commit

在提交你的更改之前，请确保过一下formatter和linter，如果是Python的话还需要过一下静态类型检
查。个人不太喜欢用pre-commit这种插件来做约束，基本全靠大家自觉了。

### Protobuf

每个接口的参数都必须是一个名称形如XyzRequest的message，对应的的返回结果必须是一个名
称形如XyzResponse的message。

同时，gRPC通讯本身就会返回一个Status，里面包含code和message，因此我们不需要再在message
消息体里面包含额外的status_code和status_message这种东西。同时Status里面的details字段也允许
我们嵌入更多自定义的信息。关于状态码和gRPC的错误处理可以参考以下文档：

- https://grpc.io/docs/guides/status-codes/^
- https://grpc.io/docs/guides/error/^


Protobuf文件的样式上我们统一遵循：https://protobuf.dev/programming-guides/style/

### Logging

##### 日志打印的一个准则是：如果线上发生事故，你可以直接通过日志来定位出错的代码位置吗？

##### 常见的一些做法包括在关键方法/分支的入口处打印一下参数，捕获到代码异常时要把错误信息打印

出来，业务流程发生异常情况也可以打印一下。然后不要打印用户的隐私信息、密码、Token等。

## Python开发规范

```
相关样板可以参考trip-chat-service/这个目录下的文件
```
### 项目管理

统一使用uv进行项目管理，如何安装和使用见相关文档https://docs.astral.sh/uv/

uv是一个非常强大的项目管理工具，常见的用法之一是用uv add foo来代替pip install
foo，这样uv会自动帮你管理具体的版本约束，并生成锁文件uv.lock。

uv还提供了uvx指令，可以用来管理工具，具体见文档https://docs.astral.sh/uv/guides/tools/

The uvx command invokes a tool without installing it.
pyproject.toml是一种更加现代化的项目元数据管理方案，与依赖、打包、构建息息相关，配合
uv一同使用。

建议在开发前阅读并理解：

- https://docs.astral.sh/uv/guides/projects/^
- https://packaging.python.org/en/latest/guides/writing-pyproject-toml/^

### Lint&Format

统一使用使用ruff进行代码的lint和format，提交前务必过一遍ruff check和ruff format。你
可以选择把ruff添加为开发依赖（通过uv add --dev ruff指令）：

```
pyproject.toml
[dependency-groups]
dev = [
"ruff>=0.14.2",
]
```
也可以直接使用uvx，即uvx ruff format和uvx ruff check --fix，这样不需要将ruff
添加为开发依赖。

```
1
2
3
4
```

### 类型检查

尽量使用类型注解以及mypy和pyright的静态类型检查功能（是的，我推荐是两个都用）。请注
意，你需要把这两个工具添加为开发依赖（通过uv add --dev mypy pyright）：

```
pyproject.toml
[dependency-groups]
dev = [
"mypy>=1.18.2",
"pyright>=1.1.406",
]
```
而不是使用uvx的方式（即uvx mypy src）。这是因为uvx mypy src的原理是快速创建一
个临时虚拟环境，然后基于这个环境执行mypy，但是你的源代码中往往导入了一些三方库，mypy等
静态类型检查工具需要能读取到这些库的函数/类的类型注解才能顺利进行分析，但是uvx mypy
src创建的那个虚拟环境里面是不会安装你依赖的这些三方库的，因此会报一大堆error。

当然，uvx也支持用--with foo --with bar 这样的选项来给临时虚拟环境附带上工具插件/依
赖，但是如果你用这种方式来添加三方库到那个临时的虚拟环境里就太麻烦了。

### Logging

遵循python logging的一般规范，一个module使用一个logger，这个logger通常声明在模块代码的开
头部分。例如在chat.conversation.default模块中：

```
Code block
import logging
```
```
logger = logging.getLogger(__name__)
```
这里这个logger的name就是chat.conversation.default，后续可以使用
logger.debug(...)这样的代码去埋点日志事件。日志消息内容的长度大部分情况下最好也控制
一下，过长的日志其实就失去可读性了。同时，日志消息的内容请好好说人话，说正常的句子，说清
楚你打印的变量是啥，发生了啥，反面教材之一就是https://github.com/FudanSELab/train-
ticket/tree/release-1.0.0里的部分日志埋点代码。

要进一步了解python logging的详细用法、工作原理等，可以阅读：

- https://docs.python.org/3/howto/logging.html#logging-basic-tutorial^
- https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial^
- https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook^

```
1 2 3 4 5 1 2 3
```

### 包名规范

微服务/Agent的名称一般形如"trip-xyz-service"、"trip-foo-bar-service"、"trip-abc-planner"，那么对
应的你要在pyproject.toml 中填入的project.name就对应分别是"xyz"、"foo-bar"、"abc-
planner"，在你的src/下的顶级包名（Namespace）就应该分别对
应"xyz"、"foo_bar"、"abc_planner"。

### Protobuf

统一将项目contracts/protobuf下的文件拷贝到具体微服务目录下的libs/proto/目录。

例如，我正在开发trip-chat-service，我要用到grpc和protobuf，那我就把contracts/protobuf/下的文
件完整拷贝到trip-chat-service/libs/proto/下。

考虑到grpcio-tools编译生成的python代码的一些机制，这里我设计了一套规范的流程来保证导包路
径不会出错：

grpcio-tools在编译.proto为python代码的时候，会按照你.proto文件所在的目录结构（当你指定了-
I参数）来对应到生成的*_pb2.py和*_pb2_grpc.py的位置。例如，我们在trip-chat-service/目录下用
以下指令编译：

```
Code block
uv run -m grpc_tools.protoc \
-Ilibs/proto \
--python_out=<output_dir> \
--grpc_python_out=<output_dir> \
libs/proto/tripsphere/**/*.proto
```
那么libs/proto/tripsphere/chat/conversation.proto这个文件会被对应编译到
<output_dir>/tripsphere/chat/conversation_pb2.py和
<output_dir>/tripsphere/chat/conversation_pb2_grpc.py，且这两个产物文件里面存在形如：

```
Code block
from tripsphere.chat import conversation_pb2 as tripsphere_dot_chat_dot_conve
```
##### 的包导入语句。

因此，我在trip-chat-service/libs/下创建一个（没有实际内容的）名为tripshere的空项目事先占位：

```
trip-chat-service/libs/tripsphere/pyproject.toml
[project]
name = "tripsphere"
version = "0.1.0"
```
```
1 2 3 4 5 1 1 2 3
```

```
readme = "README.md"
dependencies = [
"protobuf>=6.32.1",
]
```
```
[build-system]
requires = ["uv_build>=0.8.19,<0.10.0"]
build-backend = "uv_build"
```
这个项目遵循标准的src/（同时也是uv推荐的）python package结构，一开始
libs/tripsphere/src/tripsphere/下只有__init__.py和py.typed。然后我们在trip-chat-service/目录下执
行命令编译时，将grpcio-tools编译的输出目录设置为libs/tripsphere/src：

```
Code block
uv run -m grpc_tools.protoc \
-Ilibs/proto \
--python_out=libs/tripsphere/src \
--grpc_python_out=libs/tripsphere/src \
libs/proto/tripsphere/**/*.proto
```
这样上面那个例子编译的文件就对应到，trip-chat-
service/libs/tripsphere/src/tripsphere/chat/conversation_pb2.py和trip-chat-
service/libs/tripsphere/src/tripsphere/chat/conversation_pb2_grpc.py，成为libs/下tripsphere包源码
的一部分。

然后利用uv的workspace功能（创建完占位的tripsphere包后，在trip-chat-service下用uv add
tripsphere添加，pyproject.toml会自动更新），在trip-chat-service/pyproject.toml中：

```
trip-chat-service/pyproject.toml
[project]
name = "chat"
version = "0.1.0"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
"tripsphere",
]
```
```
[build-system]
requires = ["uv_build>=0.9.1,<0.10.0"]
build-backend = "uv_build"
```
```
[tool.uv.sources]
```
```
4 5 6 7 8 9
```
```
10
11
```
```
1 2 3 4 5 1 2 3 4 5 6 7 8 9
```
```
10
11
12
13
14
```

```
tripsphere = { workspace = true }
```
```
[tool.uv.workspace]
members = ["libs/tripsphere"]
```
以这样的方式引入这个编译产物（tripsphere包）作为依赖。后续在trip-chat-service/src/chat的代码
中就可以直接以类似：

```
Code block
from tripsphere.chat import conversation_pb2, conversation_pb2_grpc
```
的方式来直接使用这些grpc的接口和消息体。

需要注意的是，libs/tripsphere下编译.proto生成的*_pb2.py和*_pb2_grpc.py通通需要被gitignore，
只留下libs/tripsphere/src/tripsphere/下的__init__.py和py.typed，这也是为啥我说
tripsphere这个包在代码仓库中就只是一个空的占位用的包。libs/proto下的原始.proto文件也通通需
要被gitignore。仓库中.proto的唯一来源就是contracts/protobuf。

## Go开发规范

## Java开发规范

```
相关样板可以参考trip-note-service/目录下的文件
```
### mvnw

### 格式化

使用https://github.com/google/google-java-format进行代码的格式化，并选择AOSP Style（因为默
认的google style是两个空格缩进的，我看不习惯）。具体安装和使用方式可以自由选择，是当一个
命令行工具来使，还是作为IntelliJ的插件，都取决于你。

### 包名规范

以trip-note-service为例，pom.xml中需要统一groupId、artifactId和name等的命名规范：

```
15
16
17
18
```
```
1
```

```
Code block<groupId >org.tripsphere</groupId>^
<artifactId>trip-note-service</artifactId>
<version>0.1.0</version>
<packaging>jar</packaging>
<name>trip-note-service</name>
```
以trip-note-service为例，那么Java源代码的软件包路径大致如org.tripsphere.note.xyz.foo。同样还是
以trip-note-service为例，SpringBootApplication类名应为NoteApplication。

### Protobuf

统一将项目contracts/protobuf下的文件拷贝到具体微服务目录下的src/main/proto/下。

在pom.xml中配置好protobuf-maven-plugin后，maven protobuf compile和maven protobuf compile-
custom会把src/main/proto下的.proto文件编译到target/generated-sources/protobuf这个目录下。一
般IntelliJ会自动将其中的软件包识别为生成的源代码包，你在src/main/java里可以直接导入。但是如
果IntelliJ没有自动识别，那你就需要手动右键一下target/generated-sources/protobuf中的java和
grpc-java目录，然后将其标识为“生成的源代码”。

请注意src/main/proto下的原始.proto文件需要被gitignore。

## TypeScript开发规范

```
1
2
3
4
5
```

