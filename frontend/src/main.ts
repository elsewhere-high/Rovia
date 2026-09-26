import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import App from './App.vue'
import router from './router'
import { pinia } from './stores/pinia'
import './styles/main.css'

createApp(App).use(pinia).use(router).use(VueQueryPlugin).mount('#app')
