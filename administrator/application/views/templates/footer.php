</div> </div> <script>
// 削除確認ダイアログ
document.querySelectorAll('.btn-danger').forEach(button => {
    if (button.getAttribute('data-confirm')) {
        button.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    }
});
</script>

</body>
</html>