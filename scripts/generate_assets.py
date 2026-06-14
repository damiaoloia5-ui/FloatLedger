"""图标资源生成脚本。

运行此脚本生成应用图标文件（PNG），供 PyInstaller 打包使用。
需要 PyQt6 已安装。
"""

import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication
from ui.icon_factory import save_icon_png


def main() -> None:
    app = QApplication(sys.argv)  # QImage 保存需要 QApplication
    assets_dir = ROOT / "assets"
    assets_dir.mkdir(exist_ok=True)

    save_icon_png(str(assets_dir / "icon.png"), size=256)
    save_icon_png(str(assets_dir / "icon@2x.png"), size=512)
    save_icon_png(str(assets_dir / "icon_16.png"), size=16)
    save_icon_png(str(assets_dir / "icon_32.png"), size=32)

    print(f"图标文件已生成到 {assets_dir}/")

    # 尝试生成 ICO（需要 Pillow）
    try:
        from PIL import Image

        img = Image.open(assets_dir / "icon.png")
        # 多尺寸 ICO
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(
            str(assets_dir / "icon.ico"),
            format="ICO",
            sizes=sizes,
        )
        print(f"ICO 文件已生成到 {assets_dir}/icon.ico")
    except ImportError:
        print("Pillow 未安装，跳过 ICO 生成。安装命令: pip install Pillow")
    except Exception as exc:
        print(f"ICO 生成失败: {exc}")


if __name__ == "__main__":
    main()
