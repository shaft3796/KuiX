<img src="https://github.com/Shaft-3796/KuiX/blob/main/assets/main_dark.svg#gh-light-mode-only" height="400px">
<img src="https://github.com/Shaft-3796/KuiX/blob/main/assets/main_white.svg#gh-dark-mode-only" height="400px">

# KuiX
A powerful, modular, easy to use and scalable python algorithmic trading engine.

/!\ Highly under development, usable yet but use it at your own risk. /!\

## Abstract

Algorithmic trading is such a passioning domain. Creating trading robot can be useful to avoid trader emotions and a robot never sleep!

### Why & what?
Writing trading robot can be very boring and a lot of work is needed to automate and monitor a simple strategy, KuiX aims to provide a simple but powerful way to quickly create a highly customizable trading robot.

### For who?
KuiX is suitable for individuals who do not want to take the lead on the technical part of a trading robot while having an extendable and customizable engine if necessary.

## Project

KuiX is currently under high development, do not hesitate to follow the project to be here for the first releases! If you want to suggest some ideas or have any question, you can dm me on discord: *Shaft#3796*

#### Project Roadmap

```
- Build a functional and usable engine with handling of components.
-> Release ALPHA-1.1 [Achieved 2023-01-05]

- Typo correction, code cleaning/refacto and documentation.
- Add built-in workers components. (CCXT, persistence, ...)
- Add built-in core components. (Logging, monitoring with web ui and discord, ...)
- Add examples of strategies.
```

## Features


#### Ease of use
- Pre built strategy classes to inherit
- Pre built components (We will talk about it later.)

#### Scalability, optimization.
- Hybrid concurrency/parallelism. KuiX creates subprocess as much as available cpu to get rid of the Python Global Interpreter Lock. Threads for workers and components are then spread across processes.
- Remote process. KuiX will potentially allow to host remote processes on other computers connected to the engine to avoid running a complete engine on each computer.

#### Modularity
- KuiX is based on a Worker/Component architecture.
- All created strategies class can be instanced by the engine with different configuration, these workers are spread across subprocesses.
- Components are pre built or custom classes used to extend the engine, we talk about it in the next section.

#### Components
Components are one of the most important parts of KuiX; There is two types of components:

- Core component: these components are instanced once in the main process, they have a low level access to the engine and can be used to do a lot of tasks such as monitoring the engine or the strategies.

- Strategy components are used in strategy classes. These components are instanced when a worker is instanced. These components are used to provide strategies advanced features. For example we can create a CCXT component to let a strategy use the library, as another example we can also create a strategy component in charge of communicating with a Core component to directly log trades or strategy informations.

KuiX wants to provide as much as pre built component as possible, but users will be able to code their own components and to extend the engine as they wish!
