# VPilot: Menubar中的语音Agent

macOS menubar中的语音助手，基于[Agent TARS CLI](https://github.com/bytedance/UI-TARS-desktop)，适合语音导航任务

## 快速开始

### 配置[Agent TARS CLI](https://github.com/bytedance/UI-TARS-desktop)

下载[Agent TARS CLI](https://github.com/bytedance/UI-TARS-desktop)

```shell
npm install @agent-tars/cli@latest -g
```

[配置workspace](https://agent-tars.com/guide/basic/workspace)

```shell
agent-tars workspace --init
```

```typescript
// ~/.agent-tars-workspace/agent-tars.config.ts
import { defineConfig } from '@agent-tars/interface';

export default defineConfig({
  model: {
    provider: 'volcengine',
    id: 'doubao-1-5-thinking-vision-pro-250428',
    "apiKey": "YOUR-API-KEY"  
  }
});
```

## 安装VPilot软件

前往 [Releases](https://github.com/Shi1xin/Qiniu-Hackathon/releases) 下载 VPilot.dmg，打开后将应用拖入 `Applications` 后即可分发或安装。

## 调试与开发

```shell
gh repo clone Shi1xin/Qiniu-Hackathon
```

```shell
./Qiniu-Hackathon/run_voicebar.sh
```

## 编译为dmg

```shell
./package_dmg.sh
```