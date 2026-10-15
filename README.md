# SOLO SIEGE（Cloudflare Workers版・ログ収集つき）

- public/ … ゲーム本体
- src/ … ログを受け取るプログラム（/api/collect と /api/admin）
- wrangler.jsonc … 設定。`database_id` の所を、D1のデータベースIDに書き換える

## 手順
1. Cloudflare → Storage & databases → D1 → Create database（名前: solo-siege-logs）
2. 作ったデータベースを開き、「Database ID」をコピー
3. GitHubのリポジトリの wrangler.jsonc を開き、`ここにD1のデータベースIDを貼る` の所をそのIDに置き換えて保存（Commit）
4. Cloudflare → Workers & Pages → solo-siege-cloudflare → Settings → Variables and Secrets → Add
   - Type: Secret / Name: `ADMIN_PASS` / Value: 好きなパスワード
5. Deployments（または Builds）で再デプロイが走るのを待つ

見る画面: https://（あなたのworkers.dev）/api/admin （パスワードだけ入れる）
