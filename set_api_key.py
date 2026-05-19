import keyring
import getpass
import sys

def main():
    print("="*50)
    print("API Key Secure Setup (macOS Keychain / keyring)")
    print("="*50)
    print("このツールは、OpenAI APIキーをmacOSのキーチェーンに安全に保存します。")
    print("保存されたキーは、ソースコード上に表示されることなく自動化システムから読み込まれます。\n")
    
    api_key = getpass.getpass("OpenAI API Key を入力してください (入力内容は画面に表示されません): ")
    
    if not api_key.strip():
        print("エラー: APIキーが入力されませんでした。")
        sys.exit(1)
        
    try:
        keyring.set_password("stock_photo_system", "openai_api_key", api_key.strip())
        print("\n✅ APIキーの保存に成功しました！")
        print("今後は stock_photo_system というサービス名でキーチェーンから自動的に読み込まれます。")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
