# SOLO SIEGE を Cloudflare Pages に置く（ログ収集つき）

1. このフォルダの中身を GitHub のリポジトリのルートに置く（index.html と functions/ が直下にある形）
2. Cloudflare ダッシュボード → Workers & Pages → Create → Pages → Connect to Git → そのリポジトリ
   - Framework preset: None / Build command: 空 / Build output directory: `/`
3. データベース（D1）を作る
   - Storage & Databases → D1 → Create → 名前は何でもよい（例: solo-siege-logs）
   - Pages のプロジェクト → Settings → Bindings → Add → D1 database
     - Variable name: `DB`（この名前にする） / Database: 作ったもの
4. 管理画面のパスワードを決める
   - Settings → Variables and Secrets → Add → Name: `ADMIN_PASS` / Value: 好きなパスワード（Encryptを選ぶ）
5. 設定後に Deployments から「Retry deployment」（バインドを反映させる）

見る画面: https://（あなたのpages.dev）/api/admin （ユーザー名は何でもよく、パスワードだけ ADMIN_PASS）
テーブルは最初の送信で自動で作られる。
